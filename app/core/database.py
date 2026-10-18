from typing import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


def create_db_engine(database_url: str, echo: bool) -> AsyncEngine:
    """Crea el motor asincrónico de SQLAlchemy hacia PostgreSQL (asyncpg)."""
    return create_async_engine(database_url, echo=echo)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Crea la fábrica de sesiones asincrónicas (una sesión por petición).

    Se usa `AsyncSession` de `sqlmodel.ext.asyncio.session` (y no la de
    `sqlalchemy.ext.asyncio`) porque añade el método `.exec()` propio de
    SQLModel, que usan todos los services y el endpoint `/health/ready`.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Entrega una sesión por petición desde `request.app.state` y la cierra al final."""
    session_factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with session_factory() as session:
        yield session
