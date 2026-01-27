import json
import logging
from collections import defaultdict

from aiogram import Dispatcher
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
from ollama import Client

from config import SUBSCRIBERS_FILE, OLLAMA_HOST, OLLAMA_MODEL
from redmine import fetch_page_source
from parser import extract_last_level_rows, format_hours_report
from aiogram.types import BufferedInputFile
from praise_team import praise_team

from translations import t

# Store conversation history for each user
conversation_history: dict[int, list[dict[str, str]]] = defaultdict(list)
MAX_HISTORY_LENGTH = 10

ollama_client = Client(host=OLLAMA_HOST)


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
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard


async def send_welcome(message: Message):
    welcome_text = "Выберите действие:"
    await message.answer(welcome_text, reply_markup=get_main_keyboard())


async def subscribe(message: Message):
    await _subscription_command(message, subscribe=True)


async def unsubscribe(message: Message):
    await _subscription_command(message, subscribe=False)


async def chat_message(message: Message):
    if message.chat.type != "private":
        await message.answer(
            "📝 Пожалуйста, напишите в личные сообщения бота для общения с AI"
        )
        return

    if message.from_user is None or message.text is None:
        return

    user_id = message.from_user.id
    user_message = message.text

    conversation_history[user_id].append({"role": "user", "content": user_message})

    if len(conversation_history[user_id]) > MAX_HISTORY_LENGTH:
        conversation_history[user_id] = conversation_history[user_id][
            -MAX_HISTORY_LENGTH:
        ]

    try:
        response = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=conversation_history[user_id],
        )

        ai_message = response["message"]["content"]

        conversation_history[user_id].append(
            {"role": "assistant", "content": ai_message}
        )

        await message.answer(ai_message)

    except Exception as e:
        logging.error(f"Error in chat_message for user {user_id}: {e}")
        await message.answer("❗ Произошла ошибка при общении с AI. Попробуйте позже.")


async def praise_team_callback(callback: CallbackQuery):
    """Handle 'Praise Team' button click."""
    try:
        praise_message = praise_team()
        if callback.message:
            await callback.message.answer(praise_message)
        await callback.answer()
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in praise_team_callback: {error_msg}")

        # Check if error is related to old query timeout
        if (
            "too old" in error_msg
            or "timeout expired" in error_msg
            or "query ID is invalid" in error_msg
        ):
            await callback.answer(
                "⏰ This button has expired. Please use /check for current report.",
                show_alert=True,
            )
        else:
            await callback.answer("❗ Error sending praise", show_alert=True)


def register_handlers(dp: Dispatcher):
    dp.message.register(send_welcome, Command("start"))
    dp.message.register(manual_check, Command("check"))
    dp.message.register(subscribe, Command("subscribe"))
    dp.message.register(unsubscribe, Command("unsubscribe"))
    dp.message.register(chat_message)
    dp.callback_query.register(praise_team_callback, lambda c: c.data == "praise_team")


def get_praise_keyboard():
    """Create inline keyboard with 'Praise Team' button."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎉 Praise Team", callback_data="praise_team")]
        ]
    )
    return keyboard
