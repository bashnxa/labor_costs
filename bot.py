import asyncio
import datetime
import json
import logging
import os
from functools import partial
import holidays

from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from bs4 import BeautifulSoup

from config import (
    BOT_TOKEN,
    SCHEDULE_TIME,
    SCHEDULE_DAYS,
    SCHEDULE_MISFIRE_GRACE_TIME,
    SCHEDULE_COALESCE,
    TELEGRAM_CHAT_ID,
    LANG,
    SUBSCRIBERS_FILE,
    EMPLOYEES,
    SCHEDULE_TIME_PERSONAL,
    PROXY_URLS,
    PROXY_TEST_URL,
    PROXY_TEST_TIMEOUT,
    PROXY_ERROR_THRESHOLD,
)
from handlers import register_handlers
from parser import extract_last_level_rows, format_hours_report
from praise_team import praise_team
from redmine import fetch_page_source
from translations import t, set_language
from proxy_manager import ProxyManager

dp = Dispatcher()
scheduler = AsyncIOScheduler()
set_language(LANG)

holidays_ru = holidays.country_holidays("RU")

# Initialize proxy manager
proxy_manager = ProxyManager(
    proxy_urls=PROXY_URLS,
    test_url=PROXY_TEST_URL,
    test_timeout=PROXY_TEST_TIMEOUT,
    error_threshold=PROXY_ERROR_THRESHOLD,
)


def validate_env_vars():
    required_vars = [
        "REDMINE_LOGIN_URL",
        "REDMINE_USERNAME",
        "REDMINE_PASSWORD",
        "BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "REPORT_URL",
        "CONFIG_PATH",
        "LANG",
    ]
    for var in required_vars:
        if not os.getenv(var):
            raise OSError(f"Missing required environment variable: {var}")


validate_env_vars()


def is_working_day() -> bool:
    today = datetime.date.today()
    return today.weekday() < 5 and today not in holidays_ru


def start_scheduler(bot: Bot, SCHEDULE_TIME_PERSONALME=None) -> None:
    if is_working_day():
        scheduler.add_job(
            partial(scheduled_time_check, bot),
            trigger=CronTrigger(
                hour=SCHEDULE_TIME.hour,
                minute=SCHEDULE_TIME.minute,
                day_of_week=SCHEDULE_DAYS,
                timezone=SCHEDULE_TIME.timezone,
            ),
            misfire_grace_time=SCHEDULE_MISFIRE_GRACE_TIME,
            coalesce=SCHEDULE_COALESCE,
        )
        scheduler.add_job(
            partial(scheduled_personal_time_check, bot),
            trigger=CronTrigger(
                hour=SCHEDULE_TIME_PERSONAL.hour,
                minute=SCHEDULE_TIME_PERSONAL.minute,
                day_of_week=SCHEDULE_DAYS,
                timezone=SCHEDULE_TIME_PERSONAL.timezone,
            ),
            misfire_grace_time=SCHEDULE_MISFIRE_GRACE_TIME,
            coalesce=SCHEDULE_COALESCE,
        )
        scheduler.start()
    else:
        print("Skipping scheduler because it's a weekend or holiday.")


async def scheduled_time_check_by_user(bot, user_id, username):
    page_html: str = fetch_page_source()
    time_entries_html: str = extract_last_level_rows(page_html)

    target_name: str = ""
    for name in EMPLOYEES:
        if EMPLOYEES[name].tg == "@" + username:
            target_name = name

    if not target_name:
        return

    soup = BeautifulSoup(time_entries_html, "html.parser")
    rows = soup.find_all("tr", class_="last-level")

    target_row = None
    for row in rows:
        name_link = row.find("a")
        if name_link and name_link.get_text().strip() == target_name:
            target_row = row
            break

    if not target_row:
        return

    new_soup = BeautifulSoup("<table></table>", "html.parser")
    table = new_soup.find("table")
    if table:
        table.append(target_row)

    hours_report = format_hours_report(str(new_soup))

    if hours_report.image:
        image_file = BufferedInputFile(
            hours_report.image, filename="work_hours_chart.png"
        )
        await bot.send_photo(
            user_id,
            photo=image_file,
            caption=hours_report.text,
            parse_mode="HTML",
        )
    else:
        await bot.send_message(user_id, hours_report.text, parse_mode="HTML")


async def scheduled_personal_time_check(bot: Bot) -> None:
    with open(SUBSCRIBERS_FILE, encoding="utf-8") as f:
        subscribers_data = json.load(f)
        for user_id, user_data in subscribers_data.items():
            try:
                subscribe_status = user_data["subscribe"]
                username = user_data["username"]
                if subscribe_status:
                    await scheduled_time_check_by_user(
                        bot=bot, user_id=user_id, username=username
                    )
            except Exception as e:
                logging.error(f"Error processing user {user_id}: {e}")
                continue


async def scheduled_time_check(bot: Bot) -> None:
    try:
        page_html: str = fetch_page_source()
        time_entries_html: str = extract_last_level_rows(page_html)
        hours_report = format_hours_report(time_entries_html)

        from handlers import get_praise_keyboard

        praise_keyboard = get_praise_keyboard()

        if hours_report.has_missing:
            if hours_report.image:
                image_file = BufferedInputFile(
                    hours_report.image, filename="work_hours_chart.png"
                )
                await bot.send_photo(
                    TELEGRAM_CHAT_ID,
                    photo=image_file,
                    caption=hours_report.text,
                    parse_mode="HTML",
                    reply_markup=praise_keyboard,
                )
            else:
                await bot.send_message(
                    TELEGRAM_CHAT_ID,
                    hours_report.text,
                    parse_mode="HTML",
                    reply_markup=praise_keyboard,
                )
        else:
            await bot.send_message(
                TELEGRAM_CHAT_ID, praise_team(), reply_markup=praise_keyboard
            )
    except Exception as error:
        await bot.send_message(TELEGRAM_CHAT_ID, f"❗ {t('error')}: {error}")


async def main():
    # Initialize proxy manager and find best connection
    await proxy_manager.initialize()

    # Create bot with current connector
    connector = await proxy_manager.get_connector()
    bot = Bot(token=BOT_TOKEN, connector=connector)

    register_handlers(dp)
    start_scheduler(bot)

    # Add middleware for error tracking
    @dp.errors()
    async def error_handler(event):
        error = event.exception
        logging.error(f"Bot error: {error}")

        # Check if it's a Telegram API error that might indicate connection issues
        if "Conflict" in str(error) or "terminated by other" in str(error):
            await proxy_manager.report_error(error)

            # Check if we need to restart with new connector
            if proxy_manager.current_connector != connector:
                logging.info("Connector changed, restarting bot with new connection...")
                await bot.session.close()
                new_connector = await proxy_manager.get_connector()
                new_bot = Bot(token=BOT_TOKEN, connector=new_connector)
                register_handlers(dp)
                start_scheduler(new_bot)
                await dp.start_polling(new_bot)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        asyncio.run(proxy_manager.shutdown())
