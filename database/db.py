import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from database.models import Base
from config import config


DATABASE_URL = config.URL


engine = create_async_engine(DATABASE_URL, future=True, echo=True)


async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=True,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session: AsyncSession = async_session()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise
    finally:
        await session.close()


async def init_db(engine: AsyncEngine):
    """
    Асинхронная инициализация базы данных (создание таблиц).

    :param engine: Асинхронный движок SQLAlchemy.
    """
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("База данных успешно инициализирована.")
            return
        except Exception as e:
            print(f"Попытка {attempt + 1} неудачна: {e}")
            await asyncio.sleep(5)
            attempt += 1

    raise Exception("Не удалось подключиться к базе данных после нескольких попыток.")

