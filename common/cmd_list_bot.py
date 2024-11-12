from aiogram import Bot
from aiogram.types import BotCommand

private = [
    BotCommand(command='menu', description='Меню'),
    BotCommand(command='catalog', description='Посмотреть каталог'),
    BotCommand(command='payment', description='Способы оплаты')
]


