from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine

from app.config import settings

# 모듈 레벨 싱글턴 — 요청마다 재생성하지 않아야 connection pool이 동작한다
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker | None = None


def _build_db_url() -> str:
    url = settings.database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        db_url = _build_db_url()
        if not db_url:
            raise ValueError(
                "DATABASE_URL이 설정되지 않았습니다. 환경변수에 DATABASE_URL을 입력하세요."
            )
        _engine = create_async_engine(
            db_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    return _engine


def _get_session_maker() -> async_sessionmaker:
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_maker


async def get_db() -> AsyncSession:
    async with _get_session_maker()() as session:
        yield session
