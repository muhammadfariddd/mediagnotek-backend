from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_

from app.db.database import get_db
from app.models.drug import DrugBatch, Drug
from app.models.facility import Facility

router = APIRouter(prefix="/api/v1/batches", tags=["Drug Batches (FEFO Stock)"])


# ==================== SCHEMAS ====================
class BatchCreate(BaseModel):
    facility_id: Optional[int] = None
    kode_obat: Optional[str] = None
    nama: str
    kategori: Optional[str] = "Umum"
    golongan: Optional[str] = "Bebas"
    bentuk: Optional[str] = "Tablet"
    satuan: Optional[str] = "Strip (10 Tab)"
    stok: int
    min_stok: Optional[int] = 20
    harga_beli: float
    harga_jual: float
    batch_no: str
    expired_date: str
    lokasi_rak: Optional[str] = "Rak A-01"


class BatchUpdate(BaseModel):
    kode_obat: Optional[str] = None
    nama: Optional[str] = None
    kategori: Optional[str] = None
    golongan: Optional[str] = None
    bentuk: Optional[str] = None
    satuan: Optional[str] = None
    stok: Optional[int] = None
    min_stok: Optional[int] = None
    harga_beli: Optional[float] = None
    harga_jual: Optional[float] = None
    batch_no: Optional[str] = None
    expired_date: Optional[str] = None
    lokasi_rak: Optional[str] = None


class BatchResponse(BaseModel):
    id: int
    kode_obat: str
    nama: str
    kategori: str
    golongan: str
    bentuk: str
    satuan: str
    stok: int
    min_stok: int
    harga_beli: float
    harga_jual: float
    batch_no: str
    expired_date: str
    lokasi_rak: str


def format_batch_response(b: DrugBatch, d: Optional[Drug] = None) -> dict:
    nama = d.nama if d else f"Obat #{b.drug_id}"
    kategori = d.kategori if (d and d.kategori) else "Umum"
    bentuk = d.dosis_standar or "Tablet"
    satuan = "Strip (10 Tab)"
    golongan = "Keras" if "Keras" in (d.peringatan or "") else "Bebas"
    kode_obat = f"OBT-{b.drug_id:03d}"

    # Jika nama mengandung informasi bentuk
    if d and "(" in d.nama and ")" in d.nama:
        try:
            bentuk_part = d.nama.split("(")[-1].replace(")", "")
            satuan = bentuk_part
        except Exception:
            pass

    return {
        "id": b.id,
        "kode_obat": kode_obat,
        "nama": nama,
        "kategori": kategori,
        "golongan": golongan,
        "bentuk": bentuk,
        "satuan": satuan,
        "stok": b.stok_sisa,
        "min_stok": 20,
        "harga_beli": float(b.harga_beli_hpp),
        "harga_jual": float(b.harga_jual),
        "batch_no": b.batch_number,
        "expired_date": str(b.expired_date),
        "lokasi_rak": f"Rak {chr(65 + (b.id % 4))}-0{(b.id % 5) + 1}",
    }


# ==================== ENDPOINTS ====================
@router.get("", response_model=List[BatchResponse])
async def get_drug_batches(
    search: Optional[str] = Query(None),
    facility_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Mengambil seluruh data batch obat inventori FEFO dari database."""
    stmt = (
        select(DrugBatch, Drug)
        .outerjoin(Drug, DrugBatch.drug_id == Drug.id)
        .order_by(DrugBatch.expired_date.asc())  # Urutan FEFO First Expired First Out
    )

    if facility_id:
        stmt = stmt.where(DrugBatch.facility_id == facility_id)

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Drug.nama.ilike(search_pattern),
                DrugBatch.batch_number.ilike(search_pattern),
                Drug.kategori.ilike(search_pattern)
            )
        )

    result = await db.execute(stmt)
    rows = result.all()
    return [format_batch_response(batch, drug) for batch, drug in rows]


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_drug_batch(req: BatchCreate, db: AsyncSession = Depends(get_db)):
    """Menambahkan batch obat baru ke database inventori FEFO."""
    # Pastikan facility_id ada
    facility_id = req.facility_id
    if not facility_id:
        fac_res = await db.execute(select(Facility.id).limit(1))
        facility_id = fac_res.scalar_one_or_none() or 1

    # Cari apakah master obat sudah ada di database, jika belum buatkan
    stmt_drug = select(Drug).where(Drug.nama.ilike(req.nama.strip()))
    res_drug = await db.execute(stmt_drug)
    drug = res_drug.scalar_one_or_none()

    if not drug:
        drug = Drug(
            nama=req.nama.strip(),
            deskripsi=f"Kategori: {req.kategori or 'Umum'}. Sediaan: {req.bentuk or 'Tablet'}",
            kategori=req.kategori or "Umum",
            dosis_standar=req.bentuk or "Tablet",
            peringatan=f"Golongan: {req.golongan or 'Bebas'}"
        )
        db.add(drug)
        await db.commit()
        await db.refresh(drug)

    exp_date = datetime.strptime(req.expired_date, "%Y-%m-%d").date()

    new_batch = DrugBatch(
        facility_id=facility_id,
        drug_id=drug.id,
        batch_number=req.batch_no.strip(),
        expired_date=exp_date,
        stok_awal=req.stok,
        stok_sisa=req.stok,
        harga_beli_hpp=req.harga_beli,
        harga_jual=req.harga_jual,
        is_active=True
    )
    db.add(new_batch)
    await db.commit()
    await db.refresh(new_batch)

    return format_batch_response(new_batch, drug)


@router.put("/{batch_id}", response_model=BatchResponse)
async def update_drug_batch(batch_id: int, req: BatchUpdate, db: AsyncSession = Depends(get_db)):
    """Memperbarui informasi batch stok obat di database."""
    stmt = (
        select(DrugBatch, Drug)
        .outerjoin(Drug, DrugBatch.drug_id == Drug.id)
        .where(DrugBatch.id == batch_id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Batch obat tidak ditemukan di database.")

    batch, drug = row

    if req.stok is not None:
        batch.stok_sisa = req.stok
    if req.harga_beli is not None:
        batch.harga_beli_hpp = req.harga_beli
    if req.harga_jual is not None:
        batch.harga_jual = req.harga_jual
    if req.batch_no is not None:
        batch.batch_number = req.batch_no.strip()
    if req.expired_date is not None:
        try:
            batch.expired_date = datetime.strptime(req.expired_date, "%Y-%m-%d").date()
        except Exception:
            pass

    if drug and req.nama:
        drug.nama = req.nama.strip()
    if drug and req.kategori:
        drug.kategori = req.kategori.strip()

    await db.commit()
    await db.refresh(batch)
    if drug:
        await db.refresh(drug)

    return format_batch_response(batch, drug)


@router.delete("/{batch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_drug_batch(batch_id: int, db: AsyncSession = Depends(get_db)):
    """Menghapus batch obat dari database."""
    stmt = select(DrugBatch).where(DrugBatch.id == batch_id)
    res = await db.execute(stmt)
    batch = res.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch obat tidak ditemukan.")

    await db.delete(batch)
    await db.commit()
    return None
