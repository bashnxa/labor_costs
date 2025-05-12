import asyncio
import datetime
import os
from functools import partial
import holidays

from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore

from config import (
    BOT_TOKEN,
    SCHEDULE_TIME,
    SCHEDULE_DAYS,
    SCHEDULE_MISFIRE_GRACE_TIME,
    SCHEDULE_COALESCE,
    TELEGRAM_CHAT_ID,
    LANG,
)
from aiohttp import TCPConnector
from handlers import register_handlers
from parser import extract_last_level_rows, format_hours_report
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


def start_scheduler(bot: Bot) -> None:
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


async def scheduled_time_check(bot: Bot) -> None:
    try:
        page_html: str = fetch_page_source()
        time_entries_html: str = extract_last_level_rows(page_html)
        report_message, chart_image, has_missing_entries = format_hours_report(
            time_entries_html
        )

        if has_missing_entries:
            if chart_image:
                image_file = BufferedInputFile(
                    chart_image, filename="work_hours_chart.png"
                )
                await bot.send_photo(
                    TELEGRAM_CHAT_ID,
                    photo=image_file,
                    caption=report_message,
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    TELEGRAM_CHAT_ID, report_message, parse_mode="HTML"
                )
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
