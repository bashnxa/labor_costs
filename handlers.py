import json

from aiogram import Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

from config import SUBSCRIBERS_FILE
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


def update_subscription(user, subscribe: bool):
    subscribers_data: dict[str, dict[str, bool | str]] = {}
    with open(SUBSCRIBERS_FILE, encoding="utf-8") as f:
        subscribers_data = json.load(f)
    user_id_str = str(user.id)
    subscribers_data[user_id_str] = {"subscribe": subscribe, "username": user.username}
    if subscribers_data:
        with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
            json.dump(subscribers_data, f, ensure_ascii=False, indent=2)


async def _subscription_command(message: Message, subscribe: bool):
    if message.chat.type != "private":
        await message.answer(
            "📝 Пожалуйста, напишите эту команду в личные сообщения бота @arbeitenx_bot"
        )
        return
    update_subscription(user=message.from_user, subscribe=subscribe)
    if subscribe:
        await message.answer(
            "✅ Вы успешно подписались на получение ежедневного отчета по трудовым затратам в личные сообщения!\n"
            "❌ Чтобы отписаться, используйте команду /unsubscribe"
        )
    else:
        await message.answer(
            "✅ Вы отдписались на получение ежедневного отчета по трудовым затратам в личные сообщения!\n"
            "❌ Чтобы подписаться, используйте команду /subscribe"
        )


def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/check")],
            [KeyboardButton(text="/subscribe")],
            [KeyboardButton(text="/unsubscribe")],
        ],
        resize_keyboard=True,  # Клавиатура будет уменьшена в размере
        one_time_keyboard=False,  # Клавиатура останется после нажатия
    )
    return keyboard


async def send_welcome(message: Message):
    welcome_text = "Выберите действие:"
    await message.answer(welcome_text, reply_markup=get_main_keyboard())


async def subscribe(message: Message):
    await _subscription_command(message, subscribe=True)


async def unsubscribe(message: Message):
    await _subscription_command(message, subscribe=False)


def register_handlers(dp: Dispatcher):
    dp.message.register(send_welcome, Command("start"))
    dp.message.register(manual_check, Command("check"))
    dp.message.register(subscribe, Command("subscribe"))
    dp.message.register(unsubscribe, Command("unsubscribe"))
