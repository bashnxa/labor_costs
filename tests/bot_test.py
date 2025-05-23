import datetime
import pytest
from unittest import mock

import bot
from bot import is_working_day, scheduled_time_check, validate_env_vars
from aiogram import Bot


def test_is_working_day_weekday(mocker):
    mocker.patch("bot.datetime", wraps=datetime)
    mocker.patch("bot.holidays_ru", new=[])
    bot.datetime.date.today = lambda: datetime.date(2025, 5, 21)  # среда
    assert is_working_day() is True


def test_is_working_day_weekend(mocker):
    mocker.patch("bot.datetime", wraps=datetime)
    bot.datetime.date.today = lambda: datetime.date(2025, 5, 24)  # суббота
    assert is_working_day() is False


def test_is_working_day_holiday(mocker):
    mocker.patch("bot.datetime", wraps=datetime)
    holiday = datetime.date(2025, 1, 1)
    mocker.patch("bot.holidays_ru", new=[holiday])
    bot.datetime.date.today = lambda: holiday
    assert is_working_day() is False


@pytest.mark.asyncio
async def test_scheduled_time_check_with_image(mocker):
    fake_bot = mock.AsyncMock(spec=Bot)
    mocker.patch("bot.fetch_page_source", return_value="<html>...</html>")
    mocker.patch("bot.extract_last_level_rows", return_value="parsed_html")
    mocker.patch(
        "bot.format_hours_report", return_value=("Test report", b"image-bytes", True)
    )
    await scheduled_time_check(fake_bot)
    fake_bot.send_photo.assert_awaited_once()
    args, kwargs = fake_bot.send_photo.call_args
    assert kwargs["caption"] == "Test report"
    assert kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_scheduled_time_check_text_only(mocker):
    fake_bot = mock.AsyncMock(spec=Bot)
    mocker.patch("bot.fetch_page_source", return_value="<html>...</html>")
    mocker.patch("bot.extract_last_level_rows", return_value="parsed_html")
    mocker.patch(
        "bot.format_hours_report", return_value=("Text-only report", None, True)
    )
    await scheduled_time_check(fake_bot)
    fake_bot.send_message.assert_awaited_once_with(
        mock.ANY, "Text-only report", parse_mode="HTML"
    )


@pytest.mark.asyncio
async def test_scheduled_time_check_with_exception(mocker):
    fake_bot = mock.AsyncMock(spec=Bot)
    mocker.patch("bot.fetch_page_source", side_effect=RuntimeError("fail"))
    mocker.patch("bot.t", return_value="Ошибка")
    await scheduled_time_check(fake_bot)
    fake_bot.send_message.assert_awaited_once()
    args, _ = fake_bot.send_message.call_args
    assert "Ошибка" in args[1] or "fail" in args[1]


def test_validate_env_vars_success(monkeypatch):
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
        monkeypatch.setenv(var, "dummy")
    validate_env_vars()


def test_validate_env_vars_missing(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(
        OSError, match="Missing required environment variable: BOT_TOKEN"
    ):
        validate_env_vars()
