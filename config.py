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
REMINDER_LIMIT: float = 0.75
WEEKLY_WORK_HOURS: int = 40

TimeConfig = namedtuple("TimeConfig", ["hour", "minute", "timezone"])
SCHEDULE_TIME = TimeConfig(hour=16, minute=45, timezone=timezone("Asia/Yekaterinburg"))
SCHEDULE_TIME_PERSONAL = TimeConfig(
    hour=16, minute=40, timezone=timezone("Asia/Yekaterinburg")
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
