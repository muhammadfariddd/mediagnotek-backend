from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import diseases, drugs, diagnosis, interactions, stock

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API untuk deteksi penyakit, informasi obat, cek interaksi obat, dan prediksi stok",
)

# Tambahkan CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Izinkan semua domain frontend (ubah saat production)
    allow_credentials=True,
    allow_methods=["*"],  # Izinkan semua HTTP method
    allow_headers=["*"],
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


@app.get("/health", tags=["Root"])
async def health():
    return {"status": "ok"}
