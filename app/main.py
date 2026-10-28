from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routers import diseases, drugs, diagnosis, interactions, stock, auth, ai_chat, patients, batches

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API untuk deteksi penyakit, informasi obat, cek interaksi obat, prediksi stok, dan asisten AI",
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
app.include_router(ai_chat.router)
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(batches.router)
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


@app.get("/debug-db", tags=["Root"])
async def debug_db():
    import traceback
    from app.db.database import async_session
    from app.models import Disease, Drug
    from sqlalchemy import select, func

    report = {"db_url": settings.async_database_url}
    try:
        async with async_session() as session:
            try:
                d_c = (await session.execute(select(func.count(Disease.id)))).scalar()
                report["diseases_count"] = d_c
            except Exception as e:
                report["diseases_err"] = str(e)

            try:
                dr_c = (await session.execute(select(func.count(Drug.id)))).scalar()
                report["drugs_count"] = dr_c
            except Exception as e:
                report["drugs_err"] = str(e)
                report["drugs_trace"] = traceback.format_exc()
    except Exception as e:
        report["session_err"] = str(e)
    return report
