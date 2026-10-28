from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.db.database import get_db
from app.models.transaction import Transaction, TransactionItem

router = APIRouter(prefix="/api/v1/transactions", tags=["Transactions"])

class TransactionItemCreate(BaseModel):
    drug_id: Optional[int] = None
    nama_obat: str
    jumlah: int
    satuan: Optional[str] = "Tablet"
    harga_jual_satuan: float
    aturan_pakai: Optional[str] = None

class TransactionCreate(BaseModel):
    nomor_struk: Optional[str] = None
    nama_kasir: str
    nama_pasien: str
    dokter_perujuk: Optional[str] = None
    jenis_transaksi: Optional[str] = "BEBAS"
    total_omzet: float
    total_hpp: Optional[float] = 0.0
    laba_kotor: Optional[float] = 0.0
    margin_persen: Optional[float] = 0.0
    metode_bayar: Optional[str] = "TUNAI"
    nominal_tunai: Optional[float] = None
    nominal_kembalian: Optional[float] = None
    catatan: Optional[str] = None
    items: List[TransactionItemCreate]

@router.post("", status_code=201)
async def create_transaction(payload: TransactionCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Generate nomor_struk jika belum ada
        nomor_struk = payload.nomor_struk
        if not nomor_struk:
            now_str = datetime.now().strftime("%Y%m%d%H%M%S")
            nomor_struk = f"TRX-{now_str}"

        # Hitung HPP dan laba jika 0
        total_omzet = float(payload.total_omzet)
        total_hpp = float(payload.total_hpp or (total_omzet * 0.65)) # Estimasi HPP rata-rata jika tidak terdata
        laba_kotor = total_omzet - total_hpp
        margin_persen = (laba_kotor / total_omzet * 100) if total_omzet > 0 else 0.0

        new_trx = Transaction(
            nomor_struk=nomor_struk,
            nama_kasir=payload.nama_kasir.strip(),
            nama_pasien=payload.nama_pasien.strip(),
            dokter_perujuk=payload.dokter_perujuk,
            jenis_transaksi=payload.jenis_transaksi or "BEBAS",
            total_omzet=total_omzet,
            total_hpp=total_hpp,
            laba_kotor=laba_kotor,
            margin_persen=round(margin_persen, 2),
            metode_bayar=payload.metode_bayar or "TUNAI",
            nominal_tunai=payload.nominal_tunai,
            nominal_kembalian=payload.nominal_kembalian,
            catatan=payload.catatan
        )
        db.add(new_trx)
        await db.flush()

        for it in payload.items:
            subtotal = float(it.harga_jual_satuan * it.jumlah)
            trx_item = TransactionItem(
                transaction_id=new_trx.id,
                drug_id=it.drug_id,
                nama_obat=it.nama_obat,
                jumlah=it.jumlah,
                satuan=it.satuan or "Tablet",
                harga_jual_satuan=it.harga_jual_satuan,
                subtotal_omzet=subtotal,
                aturan_pakai=it.aturan_pakai
            )
            db.add(trx_item)

        await db.commit()
        await db.refresh(new_trx)

        return {
            "status": "success",
            "message": "Transaksi berhasil disimpan ke database apotek",
            "data": {
                "id": new_trx.id,
                "nomor_struk": new_trx.nomor_struk,
                "nama_kasir": new_trx.nama_kasir,
                "total_omzet": float(new_trx.total_omzet),
                "tanggal": new_trx.tanggal_transaksi.isoformat() if new_trx.tanggal_transaksi else datetime.now().isoformat()
            }
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan transaksi: {type(e).__name__}: {str(e)}")

@router.get("")
async def list_transactions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(Transaction).options(selectinload(Transaction.items)).order_by(desc(Transaction.tanggal_transaksi))
        count_query = select(func.count(Transaction.id))

        if search:
            query = query.where(
                (Transaction.nomor_struk.ilike(f"%{search}%")) |
                (Transaction.nama_pasien.ilike(f"%{search}%")) |
                (Transaction.nama_kasir.ilike(f"%{search}%"))
            )
            count_query = count_query.where(
                (Transaction.nomor_struk.ilike(f"%{search}%")) |
                (Transaction.nama_pasien.ilike(f"%{search}%")) |
                (Transaction.nama_kasir.ilike(f"%{search}%"))
            )

        total = (await db.execute(count_query)).scalar() or 0
        query = query.offset((page - 1) * size).limit(size)
        res = await db.execute(query)
        trxs = res.scalars().all()

        results = []
        for t in trxs:
            results.append({
                "id": t.id,
                "nomor_struk": t.nomor_struk,
                "nama_kasir": t.nama_kasir,
                "nama_pasien": t.nama_pasien,
                "dokter_perujuk": t.dokter_perujuk,
                "tanggal_transaksi": t.tanggal_transaksi.isoformat() if t.tanggal_transaksi else None,
                "jenis_transaksi": t.jenis_transaksi,
                "total_omzet": float(t.total_omzet),
                "total_hpp": float(t.total_hpp),
                "laba_kotor": float(t.laba_kotor),
                "margin_persen": float(t.margin_persen),
                "metode_bayar": t.metode_bayar,
                "items": [
                    {
                        "id": item.id,
                        "nama_obat": item.nama_obat,
                        "jumlah": item.jumlah,
                        "satuan": item.satuan,
                        "harga_jual_satuan": float(item.harga_jual_satuan),
                        "subtotal_omzet": float(item.subtotal_omzet),
                        "aturan_pakai": item.aturan_pakai
                    }
                    for item in t.items
                ]
            })

        return {
            "total": total,
            "page": page,
            "size": size,
            "items": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengambil transaksi: {type(e).__name__}: {str(e)}")
