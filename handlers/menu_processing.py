import decimal

from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_banner, orm_get_all_categories, orm_get_products_by_category, orm_get_products, \
    orm_delete_from_cart, orm_reduce_product_in_cart, orm_add_to_cart, orm_get_user_carts
from keyboards.inline import get_user_main_buttons, get_user_catalog_buttons, get_products_btns, get_user_cart
from utils.paginator import Paginator


async def main_menu(session: AsyncSession, level: int, menu_name: str):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    keyboards = get_user_main_buttons(level=level)

    return image, keyboards


async def main_catalog(session: AsyncSession, level: int, menu_name: str):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)
    categories = await orm_get_all_categories(session)
    keyboards = get_user_catalog_buttons(level=level, categories=categories)

    return image, keyboards


def pages(paginator: Paginator):
    buttons = dict()
    if paginator.has_previous():
        buttons["◀ Пред."] = "previous"

    if paginator.has_next():
        buttons["След. ▶"] = "next"

    return buttons


async def main_products(session, level, category, page):
    products = await orm_get_products_by_category(session, category_id=category)

    paginator = Paginator(products, page=page)
    product = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=product.image,
        caption=(
            f'<strong>{product.name}</strong>\n'
            f'{product.description}\n'
            f'{f"Скидка: {product.discount} %"}\nСтарая цена: <s>{round(float(product.price), 2)}₽</s>\n'
            f'Новая цена: {round(float(product.price) * (1 - product.discount / 100), 2)}₽\n'
            f'<strong>Товар {paginator.page} из {paginator.pages}</strong>\n'
            if product.discount > 0 else f'<strong>{product.name}</strong>\n{product.description}\n'
                                         f'Цена:{round(float(product.price), 2)}\n<strong>Товар {paginator.page} из {paginator.pages}</strong>'
        ),
        parse_mode='HTML'
    )

    pagination_btns = pages(paginator)

    kbds = get_products_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
        product_id=product.id,
    )

    return image, kbds


async def get_cart_content(session, user_id, product_id, page, level, menu_name):
    if menu_name == "delete":
        await orm_delete_from_cart(session, user_id, product_id)
        if page > 1:
            page -= 1
    elif menu_name == "decrement":
        is_cart = await orm_reduce_product_in_cart(session, user_id, product_id)
        if page > 1 and not is_cart:
            page -= 1
    elif menu_name == "increment":
        await orm_add_to_cart(session, user_id, product_id)

    carts = await orm_get_user_carts(session, user_id)

    if not carts:
        banner = await orm_get_banner(session, "cart")
        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>{banner.description}</strong>",
            parse_mode="HTML"
        )

        kbds = get_user_cart(
            level=level,
            page=None,
            pagination_btns=None,
            product_id=None,
        )

    else:
        paginator = Paginator(carts, page=page)

        cart = paginator.get_page()[0]
        discount_price = round(cart.product.price - (decimal.Decimal(cart.product.discount) * cart.product.price / 100),
                               2)
        cart_price = round(cart.quantity * cart.product.price, 2)
        cart_discount_price = round(cart.quantity * discount_price, 2)
        total_price = round(
            sum(cart.quantity * cart.product.price for cart in carts), 2
        )
        total_discount_price = round(
            sum(cart.quantity * (
                    cart.product.price - (decimal.Decimal(cart.product.discount) * cart.product.price / 100))
                for cart in carts), 2
        )

        if cart.product.discount > 0:
            caption = (
                f"<strong>{cart.product.name}</strong>\n"
                f"цена: <s>{cart.product.price}₽</s> {discount_price}₽\n"
                f"Количество: {cart.quantity} x {discount_price}₽ = {cart_discount_price}₽\n"
                f"Товар {paginator.page} из {paginator.pages} в корзине.\n"
                f"Общая стоимость товаров в корзине: {total_price}₽\n"
                f"Общая стоимость с учётом скидок: {total_discount_price}₽"
            )
        else:
            caption = (
                f"<strong>{cart.product.name}</strong>\n"
                f"Цена: {cart.product.price}₽\n"
                f"Количество: {cart.quantity} x {cart.product.price}₽ = {cart_price}₽\n"
                f"Товар {paginator.page} из {paginator.pages} в корзине.\n"
                f"Общая стоимость товаров в корзине: {total_price}₽\n"
                f"Общая стоимость с учётом скидок: {total_discount_price}₽"
            )

        image = InputMediaPhoto(
            media=cart.product.image,
            caption=caption,
            parse_mode='HTML'
        )

        pagination_btns = pages(paginator)

        kbds = get_user_cart(
            level=level,
            page=page,
            pagination_btns=pagination_btns,
            product_id=cart.product.id,
        )

    return image, kbds


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        page: int | None = None,
        product_id: int | None = None,
        user_id: int | None = None,
):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await main_catalog(session, level, menu_name)
    elif level == 2:
        return await main_products(session, level, category, page)
    elif level == 3:
        return await get_cart_content(session, user_id, product_id, page, level, menu_name)
