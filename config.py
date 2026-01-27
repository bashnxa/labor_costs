import json
import os

from dotenv import load_dotenv
from collections import namedtuple
from pytz import timezone

from schema import ConfigModel

load_dotenv()

REDMINE_LOGIN_URL = os.getenv("REDMINE_LOGIN_URL", "")
REDMINE_USERNAME = os.getenv("REDMINE_USERNAME", "")
REDMINE_PASSWORD = os.getenv("REDMINE_PASSWORD", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
REPORT_URL = os.getenv("REPORT_URL", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-coder")
REMINDER_LIMIT: float = 0.75

# Proxy configuration
PROXY_URLS_STR = os.getenv("PROXY_URLS", "")
PROXY_URLS = (
    [url.strip() for url in PROXY_URLS_STR.split(",") if url.strip()]
    if PROXY_URLS_STR
    else []
)
PROXY_TEST_URL = os.getenv("PROXY_TEST_URL", "https://api.telegram.org")
PROXY_TEST_TIMEOUT = float(os.getenv("PROXY_TEST_TIMEOUT", "10.0"))
PROXY_ERROR_THRESHOLD = int(os.getenv("PROXY_ERROR_THRESHOLD", "3"))
WEEKLY_WORK_HOURS: int = 40

TimeConfig = namedtuple("TimeConfig", ["hour", "minute", "timezone"])
SCHEDULE_TIME = TimeConfig(hour=16, minute=45, timezone=timezone("Asia/Yekaterinburg"))
SCHEDULE_TIME_PERSONAL = TimeConfig(
    hour=16, minute=30, timezone=timezone("Asia/Yekaterinburg")
)
SCHEDULE_DAYS = "mon-fri"
SCHEDULE_MISFIRE_GRACE_TIME = 30
SCHEDULE_COALESCE = True
SUBSCRIBERS_FILE = "C:/git/labor_costs_remote/subscribers.json"


config_path = os.getenv("CONFIG_PATH", "config.json")
with open(config_path, encoding="utf-8") as file:
    raw_config = json.load(file)
config = ConfigModel(**raw_config)
EMPLOYEES = config.employees

LANG = os.getenv("LANG", "eng")
