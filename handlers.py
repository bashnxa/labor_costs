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
        hours_report = format_hours_report(time_entries_html)
        if hours_report.image:
            image_file = BufferedInputFile(
                hours_report.image, filename="work_hours_chart.png"
            )
            await message.answer_photo(
                photo=image_file, caption=hours_report.text, parse_mode="HTML"
            )
        else:
            await message.answer(hours_report.text, parse_mode="HTML")

    except Exception as error:
        await message.answer(f"❗ {t('error')}: {error}")


def register_handlers(dp: Dispatcher):
    dp.message.register(manual_check, Command("check"))
