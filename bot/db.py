from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func, select
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(128))
    grade: Mapped[str] = mapped_column(String(10))
    phone: Mapped[str] = mapped_column(String(20))
    days: Mapped[str] = mapped_column(String(40), server_default="")
    free_time: Mapped[str] = mapped_column(String(100), server_default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


def build_engine_url(raw: str) -> URL:
    """Neon'ning standart connection string'ini asyncpg uchun moslaydi."""
    url = make_url(raw).set(drivername="postgresql+asyncpg")
    query = {
        k: v for k, v in url.query.items() if k not in ("sslmode", "channel_binding")
    }
    query["ssl"] = "require"
    return url.set(query=query)


engine = create_async_engine(
    build_engine_url(settings.database_url),
    pool_size=3,
    max_overflow=2,
    pool_pre_ping=True,   # Neon uxlab qolganda uzilgan ulanishni avtomatik tiklaydi
    pool_recycle=240,
    connect_args={
        # pooler (PgBouncer) bilan ishlashi uchun
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)
SessionMaker = async_sessionmaker(engine, expire_on_commit=False)


async def get_all_applications() -> list[Application]:
    async with SessionMaker() as session:
        result = await session.scalars(select(Application).order_by(Application.id))
        return list(result)