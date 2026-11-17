from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import Settings, get_settings
from .errors import AppError


@lru_cache(maxsize=2)
def _engine(url: str) -> AsyncEngine:
    # Supabase transaction pooler (port 6543) does not support prepared statements.
    return create_async_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
    )


async def get_session(settings: Annotated[Settings, Depends(get_settings)]) -> AsyncIterator[AsyncSession]:
    if settings.database_url is None:
        raise AppError(503, "DB_NOT_CONFIGURED", "Ma’lumotlar bazasi ulanmagan", "DATABASE_URL o‘rnatilmagan.")
    maker = async_sessionmaker(_engine(settings.database_url.get_secret_value()), expire_on_commit=False)
    async with maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]
