from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import get_settings
from app.db.database import init_db
from app.routers import diseases, drugs, diagnosis, interactions, stock

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: buat tabel jika belum ada
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API untuk deteksi penyakit, informasi obat, cek interaksi obat, dan prediksi stok",
    lifespan=lifespan,
)

# Register routers
app.include_router(diseases.router)
app.include_router(drugs.router)
app.include_router(diagnosis.router)
app.include_router(interactions.router)
app.include_router(stock.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "diseases": "/api/v1/diseases",
            "drugs": "/api/v1/drugs",
            "diagnosis": "/api/v1/diagnosis",
            "interactions": "/api/v1/interactions/check",
            "stock": "/api/v1/stock/predict",
        },
    }
