from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# start_kb = ReplyKeyboardBuilder()
# start_kb.add(
#     KeyboardButton(text='меню'),
#     KeyboardButton(text='каталог'),
#     KeyboardButton(text='способы оплаты'),
#
# )
# start_kb.adjust(2, 1)


def create_keyboard(*btns: str,
                    placeholder: str = None,
                    sizes: tuple[int] = (2,)):
    keyboard = ReplyKeyboardBuilder()
    for text in btns:
        keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(resize_keyboard=True, input_field_placeholder=placeholder)
