from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from redmine import scheduled_time_check

scheduler = AsyncIOScheduler()


def start_scheduler(bot):
    scheduler.add_job(
        lambda: scheduled_time_check(bot),
        trigger=CronTrigger(
            hour=16,
            minute=45,
            day_of_week="mon-fri",
            timezone=timezone("Asia/Yekaterinburg"),
        ),
        misfire_grace_time=30,
        coalesce=True,
    )
    scheduler.start()
