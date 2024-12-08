import os

from dotenv import load_dotenv, find_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from common.texts_for_db import description_for_info_pages
from database.models import Base
from database.orm_query import orm_add_banner_description

load_dotenv(find_dotenv())

engine = create_async_engine(os.getenv('DB_URL'), echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await orm_add_banner_description(session, description_for_info_pages)
