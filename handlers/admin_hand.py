from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter

from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.orm_query import orm_add_product, orm_update_product
from keyboards.reply import create_keyboard
from keyboards.inline import callback_buttons
from filters.chat_types import ChatTypeFilter, IsAdmin

from database.orm_query import (
    orm_get_products,
    orm_delete_product,
    orm_get_product
)

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(['private']), IsAdmin())

ADMIN_KEYBOARD = create_keyboard('добавить товар',
                                 'список товаров',
                                 placeholder='выберите действие',
                                 sizes=(2,))

ADD_KEYBOARD = create_keyboard(
    'назад',
    'отмена',
    sizes=(1,)
)

CANCELLATION = create_keyboard(
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


@admin_router.message(Command('admin'))
async def admin_cmd(message: types.Message):
    await message.answer('Здравствуйте Администратор! что хотите сделать?', reply_markup=ADMIN_KEYBOARD)


@admin_router.message(F.text == 'список товаров')
async def list_product(callback: types.CallbackQuery, session: AsyncSession):
    products = await orm_get_products(session)
    if not products:
        await callback.answer('Список товаров пуст 😔')
        return
    for product in products:
        await callback.answer_photo(
            product.image,
            caption=f'<strong>{product.name}</strong>\nОписание: {product.description}\
                    \nСтоимость: {round(product.price, 2)}\
                    \nСкидка: {product.discount if product.discount != 0 else "Скидки нет"}\
                    \nКоличество: {product.quantity}',
            reply_markup=callback_buttons(
                buttons={
                    'удалить': f'delete_{product.id}',
                    'изменить': f'change_{product.id}'
                }
            ),
            parse_mode='HTML'
        )

    await callback.answer('Вот список товаров 👆', parse_mode='HTML')


@admin_router.callback_query(F.data.startswith('delete_'))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = int(callback.data.split('_')[-1])
    await orm_delete_product(session, product_id)
    print(product_id)

    await callback.answer('Товар успешно удален!')
    await callback.message.answer(f'Товар успешно удален!')


# Работа с обновлением данных


class UpdateProductStates(StatesGroup):
    update_name = State()
    update_description = State()
    update_price = State()
    update_discount = State()
    update_quantity = State()
    update_image = State()


@admin_router.callback_query(F.data.startswith('change_'))
async def update_product(callback: types.CallbackQuery, session: AsyncSession):
    change_id = int(callback.data.split('_')[-1])
    buttons = callback_buttons(buttons={
        'название': f'update_name_{change_id}',
        'описание': f'update_description_{change_id}',
        'цена': f'update_price_{change_id}',
        'скидка': f'update_discount_{change_id}',
        'количество': f'update_quantity_{change_id}',
        'изображение': f'update_image_{change_id}',
    },
        sizes=(2,)
    )

    await callback.message.answer('выберите,что хотите изменить ', reply_markup=buttons)


@admin_router.message(StateFilter('*'), F.text.casefold() == 'отмена')
async def cancellation_update_product(message: types.Message, state: FSMContext):
    current_state = await state.get_state()  # Получаем текущее состояние
    if current_state is None:  # Проверка на случай, если состояние отсутствует
        return

    await state.clear()  # Очищаем состояние
    await message.answer('Изменение товара отменено', reply_markup=ADMIN_KEYBOARD)  # Уведомление об отмене


@admin_router.callback_query(F.data.startswith('update_'))
async def update_option(callback: types.CallbackQuery, state: FSMContext):
    action, product_id = callback.data.split('_')[1], int(callback.data.split('_')[-1])
    await state.update_data(product_id=product_id)

    prompts = {
        'update_name': 'Введите новое название товара',
        'update_description': 'Введите новое описание товара',
        'update_price': 'Введите новую цену товара',
        'update_discount': 'Введите новую скидку товара',
        'update_quantity': 'Введите новое количество товара',
        'update_image': 'Отправьте новое изображение товара',
    }
    await callback.message.answer(prompts[f'update_{action}'], reply_markup=CANCELLATION)
    await state.set_state(getattr(UpdateProductStates, f'update_{action}'))


@admin_router.message(StateFilter(UpdateProductStates))
async def update_product_handler(message: types.Message, session: AsyncSession, state: FSMContext):
    data = await state.get_data()
    product_id = data.get('product_id')

    current_state = await state.get_state()
    action = current_state.split('_')[1]

    new_value = message.text
    if action in ['price', 'discount']:
        new_value = float(new_value)
    elif action in ['quantity']:
        new_value = int(new_value)
    elif action in ['image']:
        new_value = message.photo[-1].file_id
    updated_product = await orm_update_product(session, product_id, **{action: new_value})
    print(f"Updating product {product_id} - action: {action}, new_value: {new_value}")

    if updated_product:
        await message.answer_photo(
            updated_product.image,
            caption=f'<strong>{updated_product.name}</strong>\n'
                    f'Описание: {updated_product.description}\n'
                    f'Стоимость: {round(updated_product.price, 2)}\n'
                    f'Скидка: {updated_product.discount if updated_product.discount != 0 else "Скидки нет"}\n'
                    f'Количество: {updated_product.quantity}',
            reply_markup=callback_buttons(
                buttons={
                    'удалить': f'delete_{updated_product.id}',
                    'изменить': f'change_{updated_product.id}'
                }
            ),
            parse_mode='HTML'
        )
    else:
        await message.answer('Товар не найден.')

    await message.answer(f"{action.capitalize()} товара успешно обновлено!", reply_markup=ADMIN_KEYBOARD)
    await state.clear()


# работа c FSM

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
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    image = message.photo[-1].file_id
    await state.update_data(image=image)
    data = await state.get_data()
    await orm_add_product(session, data)
    await message.answer('Товар успешно добавлен!', reply_markup=ADMIN_KEYBOARD)
    await state.clear()
