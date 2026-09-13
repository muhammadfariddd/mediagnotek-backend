import ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# Neon memerlukan SSL
connect_args = {}
db_url = settings.async_database_url
if "neon.tech" in db_url or "neon" in db_url:
    ssl_context = ssl.create_default_context()
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    connect_args=connect_args,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
