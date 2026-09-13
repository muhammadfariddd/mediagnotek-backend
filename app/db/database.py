from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings
import urllib.parse
import ssl

settings = get_settings()

db_url = settings.async_database_url

# Bersihkan ?sslmode=require dari URL agar tidak diteruskan sebagai argument yang salah ke driver
if "?" in db_url:
    base_url, query_str = db_url.split("?", 1)
    # Parse query parameters
    query_params = urllib.parse.parse_qs(query_str)
    # Hapus sslmode jika ada
    if 'sslmode' in query_params:
        del query_params['sslmode']
    
    # Reconstruct url
    if query_params:
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        db_url = f"{base_url}?{new_query}"
    else:
        db_url = base_url

connect_args = {}
# Aktifkan SSL secara aman via connect_args jika ini database cloud (neon)
if "neon.tech" in db_url or "neon" in settings.DATABASE_URL:
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
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
