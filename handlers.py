from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from redmine import fetch_page_source
from parser import extract_last_level_rows, format_hours_report


async def manual_check(message: Message):
    page_html = fetch_page_source()
    time_entries_html = extract_last_level_rows(page_html)
    report_message, _ = format_hours_report(time_entries_html)
    await message.answer(report_message, parse_mode="HTML")


def register_handlers(dp: Dispatcher):
    dp.message.register(manual_check, Command("check"))
