from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings


def _build_db_url() -> str:
    url = settings.database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _get_engine():
    db_url = _build_db_url()
    if not db_url:
        raise ValueError(
            "DATABASE_URL이 설정되지 않았습니다. 환경변수에 DATABASE_URL을 입력하세요."
        )
    return create_async_engine(db_url, echo=settings.debug, pool_pre_ping=True)


def _get_session_maker():
    return async_sessionmaker(
        bind=_get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_db() -> AsyncSession:
    async with _get_session_maker()() as session:
        yield session
