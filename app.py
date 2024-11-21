import asyncio
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram import types
from dotenv import find_dotenv, load_dotenv

from handlers.user_hand import user_router
from handlers.group_hand import group_router
from handlers.admin_hand import admin_router
from database.engine import create_database, session_maker
from middlewares.db import DataBaseSession

from common.cmd_list_bot import private

load_dotenv(find_dotenv())

bot = Bot(token=os.getenv('TOKEN'))
bot.admins_list = []
dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(group_router)
dp.include_router(admin_router)


async def on_startup(bot):
    await create_database()


async def main():
    dp.startup.register(on_startup)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
