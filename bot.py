import asyncio
from aiogram import Bot, Dispatcher
from scheduler import start_scheduler
from config import BOT_TOKEN
from handlers import register_handlers

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def main():
    register_handlers(dp)
    start_scheduler(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
