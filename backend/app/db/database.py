from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings

# postgresql+asyncpg:// 형식으로 변환 (Supabase는 postgresql:// 로 제공)
_db_url = settings.database_url
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)

if not _db_url:
    raise ValueError(
        "DATABASE_URL이 설정되지 않았습니다. .env 파일에 DATABASE_URL을 입력하세요."
    )

engine = create_async_engine(
    _db_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
