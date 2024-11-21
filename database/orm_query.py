from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from database.models import Product


async def orm_add_product(session: AsyncSession, data: dict):
    objects = Product(
        name=data['name'],
        description=data['description'],
        price=float(data['price']),
        discount=float(data['discount']),
        quantity=int(data['quantity']),
        image=data['image'],
    )
    session.add(objects)
    await session.commit()


async def orm_get_products(session: AsyncSession):
    result = await session.execute(select(Product))
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
