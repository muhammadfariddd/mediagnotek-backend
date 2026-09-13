from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models import Drug, StockPrediction
from app.schemas import StockPredictRequest, StockPredictionOut

router = APIRouter(prefix="/api/v1/stock", tags=["Stock Prediction"])


@router.post("/predict", response_model=list[StockPredictionOut])
async def predict_stock(req: StockPredictRequest, db: AsyncSession = Depends(get_db)):
    """
    Prediksi kebutuhan stok obat berdasarkan data historis (simulasi).
    Menggunakan data sintetis yang mengikuti pola epidemiologi
    dari Profil Kesehatan Indonesia.
    """
    # Cek apakah obat ada
    drug = await db.execute(select(Drug).where(Drug.id == req.drug_id))
    drug = drug.scalar_one_or_none()
    if not drug:
        raise HTTPException(status_code=404, detail="Obat tidak ditemukan")

    # Ambil data stok yang sudah ada
    query = (
        select(StockPrediction)
        .where(StockPrediction.drug_id == req.drug_id)
        .order_by(StockPrediction.tanggal.desc())
        .limit(req.period_days)
    )
    result = await db.execute(query)
    stocks = result.scalars().all()

    return [
        StockPredictionOut(
            drug_id=s.drug_id,
            drug_nama=drug.nama,
            tanggal=s.tanggal,
            stok_masuk=s.stok_masuk,
            stok_keluar=s.stok_keluar,
            sisa=s.sisa,
        )
        for s in stocks
    ]
