from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from redmine import fetch_page_source
from parser import extract_last_level_rows, format_hours_report
from aiogram.types import BufferedInputFile

from translations import t


async def manual_check(message: Message):
    try:
        page_html = fetch_page_source()
        time_entries_html = extract_last_level_rows(page_html)
        report_message, chart_image, _ = format_hours_report(time_entries_html)
        if chart_image:
            image_file = BufferedInputFile(chart_image, filename="work_hours_chart.png")
            await message.answer_photo(
                photo=image_file, caption=report_message, parse_mode="HTML"
            )
        else:
            await message.answer(report_message, parse_mode="HTML")

    except Exception as error:
        await message.answer(f"❗ {t('error')}: {error}")


def register_handlers(dp: Dispatcher):
    dp.message.register(manual_check, Command("check"))
