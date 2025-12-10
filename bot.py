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
)
from aiohttp import TCPConnector
from handlers import register_handlers
from parser import extract_last_level_rows, format_hours_report
from praise_team import praise_team
from redmine import fetch_page_source
from translations import t, set_language

dp = Dispatcher()
scheduler = AsyncIOScheduler()
set_language(LANG)

holidays_ru = holidays.country_holidays("RU")


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
    for row in rows:
        name_link = row.find("a")
        if name_link and name_link.get_text().strip() == target_name:
            for sibling in row.find_previous_siblings():
                if sibling.name == "tr" and "last-level" in sibling.get("class", []):
                    sibling.decompose()
            for sibling in row.find_next_siblings():
                if sibling.name == "tr" and "last-level" in sibling.get("class", []):
                    sibling.decompose()
            break

    hours_report = format_hours_report(str(soup))
    if not hours_report.text:
        await bot.send_message(
            user_id, hours_report.text.split("\n")[0], parse_mode="HTML"
        )
        if username not in hours_report.text and (target_name in hours_report.text):
            await bot.send_message(user_id, praise_team())


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
                )
            else:
                await bot.send_message(
                    TELEGRAM_CHAT_ID, hours_report.text, parse_mode="HTML"
                )
        else:
            await bot.send_message(TELEGRAM_CHAT_ID, praise_team())
    except Exception as error:
        await bot.send_message(TELEGRAM_CHAT_ID, f"❗ {t('error')}: {error}")


async def main():
    connector = TCPConnector(ttl_dns_cache=300)
    bot = Bot(token=BOT_TOKEN, connector=connector)

    register_handlers(dp)
    start_scheduler(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
