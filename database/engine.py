import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


engine = create_async_engine(os.getenv('ENGINE'), echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)