from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply import create_keyboard
from filters.chat_types import ChatTypeFilter, IsAdmin

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(['private']), IsAdmin())

ADMIN_KEYBOARD = create_keyboard('добавить товар',
                                 'список товаров',
                                 'удалить товар',
                                 'изменить товар',
                                 placeholder='выберите действие',
                                 sizes=(2,))


@admin_router.message(Command('admin'))
async def admin_cmd(message: types.Message):
    await message.answer('Здравствуйте Администратор! что хотите сделать?', reply_markup=ADMIN_KEYBOARD)


@admin_router.message(F.text == 'список товаров')
async def list_product(message: types.Message):
    await message.answer('Вот список товаров:')


@admin_router.message(F.text == 'удалить товар')
async def delite_product(message: types.Message):
    await message.answer('удаляем товар...')


@admin_router.message(F.text == 'изменить товар')
async def update_product(message: types.Message):
    await message.answer('изменяем товар... ')


# работа c FSM

ADD_KEYBOARD = create_keyboard(
    'назад',
    'отмена',
    sizes=(1,)
)


class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    discount = State()
    quantity = State()
    image = State()

    texts = {
        'AddProduct:name': 'Введите название заново',
        'AddProduct:description': 'Введите описание заново',
        'AddProduct:price': 'Введите цену заново',
        'AddProduct:discount': 'Введите скидку заново',
        'AddProduct:quantity': 'Введите количество заново',
    }


@admin_router.message(StateFilter(None), F.text == 'добавить товар')
async def add_product(message: types.Message, state: FSMContext):
    await message.answer('Введите название товара.\nДлинна названия не должна быть меньше двух символом и не больше 50',
                         reply_markup=ADD_KEYBOARD,
                         )
    await state.set_state(AddProduct.name)


@admin_router.message(StateFilter('*'), F.text.casefold() == 'отмена')
async def cancellation_add_product(message: types.Message, state: FSMContext):
    current_state = state.get_state()
    if current_state is None:
        return

    await state.clear()
    await message.answer('Отмена добавления товара', reply_markup=ADMIN_KEYBOARD)


@admin_router.message(StateFilter('*'), F.text.casefold() == 'назад')
async def back_step_add_product(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == AddProduct.name:
        await message.answer('Предыдущего шага нет, или введите название товара или напишите "отмена"'
                             )
        return
    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"Ок, вы вернулись к прошлому шагу \n {AddProduct.texts[previous.state]}"
            )
            return
        previous = step


@admin_router.message(F.text, AddProduct.name)
async def add_name(message: types.Message, state: FSMContext):
    name = message.text
    if len(name) < 3 or len(name) > 50:
        await message.answer('длина названия должна быть больше двух и меньше 50\nВведите название снова')
        return
    await state.update_data(name=name)
    await message.answer('Теперь введите описание товара')
    await state.set_state(AddProduct.description)


@admin_router.message(AddProduct.description, F.text)
async def add_description(message: types.Message, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await message.answer('Теперь введите цену товара в рублях ₽')
    await state.set_state(AddProduct.price)


@admin_router.message(AddProduct.price, F.text)
async def add_price(message: types.Message, state: FSMContext):
    price = message.text
    try:
        price = float(price)
        if price <= 0:
            await message.answer('Цена товара должна быть больше нуля\nВведите стоимость снова')
            return
        await state.update_data(price=price)
        await message.answer('Теперь введите скидку на товар в процентах (%)\nЕсли скидки нет, отправьте "0" ')
        await state.set_state(AddProduct.discount)
    except ValueError:
        await message.answer('Введено неверное значение цены\nВведите стоимость снова')
        return


@admin_router.message(AddProduct.discount, F.text)
async def add_discount(message: types.Message, state: FSMContext):
    discount = message.text
    try:
        discount = float(discount)
        if discount < 0 or discount > 100:
            await message.answer('Скидка должна быть не меньше 0 и не больше 100\nВведите скидку снова')
            return
        await state.update_data(discount=discount)
        await message.answer('Теперь введите кол-во товаров')
        await state.set_state(AddProduct.quantity)
    except ValueError:
        await message.answer('Введено неверное значение скидки\nВведите скидку снова')
        return


@admin_router.message(AddProduct.quantity, F.text)
async def add_quantity(message: types.Message, state: FSMContext):
    quantity = message.text
    try:
        quantity = int(quantity)
        if quantity <= 0:
            await message.answer('Кол-во товаров должно быть больше нуля\nВведите кол-во снова')
            return
        await state.update_data(quantity=quantity)
        await message.answer('Загрузите изображение товара')
        await state.set_state(AddProduct.image)
    except ValueError:
        await message.answer('Введено неверное значение кол-ва товаров\nВведите кол-во снова')
        return


@admin_router.message(AddProduct.image, F.photo)
async def add_image(message: types.Message, state: FSMContext):
    image = message.photo[-1].file_id
    await state.update_data(image=image)
    await message.answer('Товар успешно добавлен!', reply_markup=ADMIN_KEYBOARD)
    # data = await state.get_data()
    # await message.answer(str(data))
    await state.clear()
