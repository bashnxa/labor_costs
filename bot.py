import asyncio
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
    TELEGRAM_CHAT_ID, LANG,
)
from handlers import register_handlers
from parser import extract_last_level_rows, format_hours_report
from redmine import fetch_page_source
from translations import t, set_language

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
set_language(LANG)


def start_scheduler() -> None:
    scheduler.add_job(
        scheduled_time_check,
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


async def scheduled_time_check() -> None:
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
    register_handlers(dp)
    start_scheduler()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
