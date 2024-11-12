from aiogram.filters import CommandStart, or_f, Command
from aiogram import types, Router
from aiogram import Bot, types, F

from filters.chat_types import ChatTypeFilter

from keyboards.reply import create_keyboard

user_router = Router()
user_router.message.filter(ChatTypeFilter(['private']))

USER_KEYBOARD = create_keyboard('меню', 'каталог', 'способы оплаты',
                                placeholder='что вас интересует',
                                sizes=(2,))


@user_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer('Добро пожаловать в наш магазин!\nЯ виртуальный помощник.\nЧто хотите сделать?',
                         reply_markup=USER_KEYBOARD
                         )


@user_router.message(or_f(F.text.lower() == 'меню', Command('menu')))
async def menu_cmd(message: types.Message):
    await message.answer('вот вам меню:\n1...\n2...\n3...')


@user_router.message(or_f(F.text.lower() == 'каталог', Command('catalog')))
async def catalog_cmd(message: types.Message):
    await message.answer('Вот каталог товаров')


@user_router.message(or_f(F.text.lower().contains('плат'), Command('payment')))
async def payment_cmd(message: types.Message):
    await message.answer('оплата производится банковской картой или QR-кодом')
