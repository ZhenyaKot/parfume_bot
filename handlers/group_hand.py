from aiogram import Router
from aiogram import types, Bot
from aiogram.filters import Command

from filters.chat_types import ChatTypeFilter

group_router = Router()
group_router.message.filter(ChatTypeFilter(['group', 'supergroup']))
group_router.edited_message.filter(ChatTypeFilter(['group', 'supergroup']))


@group_router.message(Command('admin'))
async def get_admin(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)
    admins_list = [member.user.id for member in admins_list if member.status == 'admin' or member.status == 'creator']

    bot.admins_list = admins_list
    if message.from_user.id in admins_list:
        await message.delete()