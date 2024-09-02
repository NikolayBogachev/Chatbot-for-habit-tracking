from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config import URL


# Параметры подключения к базе данных PostgreSQL
DATABASE_URL = URL

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(DATABASE_URL, future=True, echo=True)

# Создание асинхронной сессии SQLAlchemy
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