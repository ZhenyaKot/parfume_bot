from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def callback_buttons(*,
                     buttons: dict[str, str],
                     sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))
    return keyboard.adjust(*sizes).as_markup()


def get_user_main_buttons(sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    buttons = {
        "Товары 👜": "catalog",
        "Корзина 🗑": "cart",
        "О нас ℹ️": "about",
        "Оплата 💰": "payment",
        "Доставка 🚛": "shipping",
    }
    for text, data in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()