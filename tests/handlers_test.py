import pytest
from aiogram.types import Message
from handlers import manual_check


@pytest.mark.asyncio
async def test_manual_check_success(mocker):
    mocker.patch("handlers.fetch_page_source", return_value="<html>sample</html>")
    mocker.patch("handlers.extract_last_level_rows", return_value="parsed_html")

    mocked_format = mocker.patch("handlers.format_hours_report")
    mocked_format.return_value = ("<b>Report text</b>", b"fake_image_data", None)

    mock_message = mocker.Mock(spec=Message)
    mock_message.answer_photo = mocker.AsyncMock()
    mock_message.answer = mocker.AsyncMock()

    await manual_check(mock_message)

    mock_message.answer_photo.assert_called_once()
    args, kwargs = mock_message.answer_photo.call_args
    assert "Report text" in kwargs["caption"]
    assert kwargs["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_manual_check_text_only(mocker):
    mocker.patch("handlers.fetch_page_source", return_value="<html>sample</html>")
    mocker.patch("handlers.extract_last_level_rows", return_value="parsed_html")

    mocked_format = mocker.patch("handlers.format_hours_report")
    mocked_format.return_value = ("<b>Report no image</b>", None, None)

    mock_message = mocker.Mock(spec=Message)
    mock_message.answer = mocker.AsyncMock()

    await manual_check(mock_message)

    mock_message.answer.assert_called_once_with(
        "<b>Report no image</b>", parse_mode="HTML"
    )


@pytest.mark.asyncio
async def test_manual_check_error_handling(mocker):
    mocker.patch(
        "handlers.fetch_page_source", side_effect=RuntimeError("Redmine error")
    )
    mock_message = mocker.Mock(spec=Message)
    mock_message.answer = mocker.AsyncMock()

    mocker.patch("handlers.t", return_value="Ошибка")

    await manual_check(mock_message)

    mock_message.answer.assert_called_once()
    args, kwargs = mock_message.answer.call_args
    assert "Ошибка" in args[0] or "Redmine error" in args[0]
