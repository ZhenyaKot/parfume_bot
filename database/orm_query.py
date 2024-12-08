from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload, joinedload
from database.models import Product, Category, Banner, User, Cart


# работа с продуктами


async def orm_add_product(session: AsyncSession, data: dict):
    objects = Product(
        name=data['name'],
        description=data['description'],
        category_id=data['category_id'],
        price=float(data['price']),
        discount=float(data['discount']),
        quantity=int(data['quantity']),
        image=data['image'],
    )
    session.add(objects)
    await session.commit()


async def orm_get_products(session: AsyncSession):
    result = await session.execute(select(Product).options(selectinload(Product.category)))
    return result.scalars().all()


async def orm_get_products_by_category(session: AsyncSession, category_id: int):
    result = await session.execute(
        select(Product).options(selectinload(Product.category)).where(Product.category_id == category_id))
    return result.scalars().all()


async def orm_get_product(session: AsyncSession, product_id: int):
    result = await session.execute(select(Product).where(Product.id == product_id))
    return result.scalar()


async def orm_delete_product(session: AsyncSession, product_id: int):
    await session.execute(delete(Product).where(Product.id == product_id))
    await session.commit()


async def orm_update_product(
        session: AsyncSession,
        product_id: int,
        name: str = None,
        description: str = None,
        price: float = None,
        discount: float = None,
        quantity: int = None,
        image: str = None
):
    update_values = {}
    if name is not None:
        update_values['name'] = name
    if description is not None:
        update_values['description'] = description
    if price is not None:
        update_values['price'] = price
    if discount is not None:
        update_values['discount'] = discount
    if quantity is not None:
        update_values['quantity'] = quantity
    if image is not None:
        update_values['image'] = image

    if not update_values:
        return

    stmt = update(Product).where(Product.id == product_id).values(**update_values)
    await session.execute(stmt)
    await session.commit()

    stmt_get = select(Product).where(Product.id == product_id)
    result = await session.execute(stmt_get)
    updated_product = result.scalar_one_or_none()
    return updated_product


# работа с категориями

async def orm_get_all_categories(session: AsyncSession):
    result = await session.execute(select(Category))
    return result.scalars().all()


async def orm_get_category(session: AsyncSession, category_id: int):
    result = await session.execute(select(Category).where(Category.id == category_id))
    return result.scalar()


async def orm_add_category(session: AsyncSession, name: str):
    objects = Category(name=name)
    session.add(objects)
    await session.commit()


async def orm_delete_category(session: AsyncSession, category_id: int):
    await session.execute(delete(Category).where(Category.id == category_id))
    await session.commit()


# Работа с баннерами

async def orm_get_all_banners(session: AsyncSession):
    result = await session.execute(select(Banner))
    return result.scalars().all()


async def orm_add_banner_description(session: AsyncSession, data: dict):
    result = await session.execute(select(Banner))
    if result.first():
        return
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    await session.execute(update(Banner).where(Banner.name == name).values(image=image))
    await session.commit()


async def orm_get_banner(session: AsyncSession, page: str):
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


# добавление user

async def orm_add_user(session: AsyncSession, user_id: int, first_name: str = None, last_name: str = None,
                       phone: str = None):
    user = await session.execute(select(User).where(User.user_id == user_id))
    if user.first() is None:
        session.add(User(user_id=user_id, first_name=first_name, last_name=last_name, phone=phone)
                    )
        await session.commit()


# работа с корзиной

async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int):
    cart = await session.execute(select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id))
    cart = cart.scalar()
    if cart:
        cart.quantity += 1
        await session.commit()
        return cart
    else:
        session.add(Cart(user_id=user_id, product_id=product_id, quantity=1))
        await session.commit()


async def orm_get_user_carts(session: AsyncSession, user_id: int):
    query = select(Cart).filter(Cart.user_id == user_id).options(selectinload(Cart.product))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: int):
    query = delete(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    await session.execute(query)
    await session.commit()


async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int):
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        return
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        return False
