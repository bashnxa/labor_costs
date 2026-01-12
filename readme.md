# Redmine Work Hours Tracker Bot

![Telegram Bot Report Example](https://github.com/bashnxa/labor_costs/blob/main/assets/bot_report_example.png?raw=true)

## 🛠 Overview
This **Telegram bot** automates tracking work hours in **Redmine**. It scrapes data from Redmine reports using **Selenium** and **BeautifulSoup**, then formats and sends work hour reports via Telegram. The bot also reminds employees to log their hours if they fall below the expected threshold.

⚠ **Warning:** This bot is configured for a **custom Redmine report**. If you use a different Redmine setup, you must **modify the report parsing logic** in the code to match your report's structure.

⚠ **Warning:** The bot sends error messages to a Telegram chat. Do not connect it to public groups, as confidential data from Redmine may be exposed.

## 🚀 Features
- **Automated Redmine login** using Selenium
- **Daily scheduled reports** of logged work hours (sent to group chat)
- **Personal daily reports** for subscribed employees (sent to private messages)
- **Custom reminders** for employees who haven't logged enough time
- **Manual report check** via the `/check` command in Telegram
- **Subscribe/Unsubscribe** to personal daily reports
- **Configurable employee work rates**
- **Vacation support** - automatically adjusts expected work hours

## 💡 Follow on Telegram
Get bite-sized Python tips, best practices and refactoring tricks
👉 [t.me/py_snack](https://t.me/py_snack)

## 📱 Telegram Bot Commands

| Command | Description | Availability |
|---------|-------------|--------------|
| `/start` | Display main menu with available commands | All chats |
| `/check` | Manually check and display current work hours report | All chats |
| `/subscribe` | Subscribe to daily personal work hours report (sent to private messages) | Private chats only |
| `/unsubscribe` | Unsubscribe from daily personal work hours report | Private chats only |
| Any message | Chat with AI assistant using Ollama model (works in private messages only) | Private chats only |

## ⏰ Scheduled Reports

The bot runs two scheduled tasks on working days (Monday-Friday, excluding Russian holidays):

- **Group Report**: Sent to the configured Telegram chat at 16:45 (Asia/Yekaterinburg)
- **Personal Reports**: Sent to subscribed users at 16:30 (Asia/Yekaterinburg)

Schedule times can be configured in `config.py` via `SCHEDULE_TIME` and `SCHEDULE_TIME_PERSONAL` variables.

## 🤖 AI Chat (Ollama)

The bot includes an AI chat feature powered by **Ollama**. Users can chat with the AI assistant in private messages using the `/chat` command.

### Setup Ollama

1. Install Ollama: https://ollama.com/download
2. Pull the model (default: `deepseek-coder`):
   ```bash
   ollama pull deepseek-coder
   ```
3. Configure environment variables in `.env`:
   ```
   OLLAMA_HOST = "http://localhost:11434"
   OLLAMA_MODEL = "deepseek-coder"
   ```

### Usage

- Send any message in private messages to chat with AI
- The bot maintains conversation history for each user (up to 10 messages)
- Available only in private chats
