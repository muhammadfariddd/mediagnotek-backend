import json
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_

from app.db.database import get_db
from app.models.patient import Patient
from app.models.facility import Facility

router = APIRouter(prefix="/api/v1/patients", tags=["Patients Management"])


# ==================== SCHEMAS ====================
class PatientCreate(BaseModel):
    facility_id: Optional[int] = None
    nomor_rm: Optional[str] = None
    nama_lengkap: str
    nik: Optional[str] = None
    tanggal_lahir: Optional[str] = None
    jenis_kelamin: Optional[str] = "L"
    no_hp: Optional[str] = None
    alamat: Optional[str] = None
    alergi_obat: Optional[List[str]] = []
    riwayat_penyakit: Optional[List[str]] = []
    catatan_medis: Optional[str] = None
    waktu_kunjungan: Optional[str] = None
    penyakit_diderita: Optional[str] = None
    status_pembelian: Optional[str] = "Lunas"
    keterangan_pembelian: Optional[str] = None


class PatientUpdate(BaseModel):
    nama_lengkap: Optional[str] = None
    nik: Optional[str] = None
    tanggal_lahir: Optional[str] = None
    jenis_kelamin: Optional[str] = None
    no_hp: Optional[str] = None
    alamat: Optional[str] = None
    alergi_obat: Optional[List[str]] = None
    riwayat_penyakit: Optional[List[str]] = None
    catatan_medis: Optional[str] = None
    waktu_kunjungan: Optional[str] = None
    penyakit_diderita: Optional[str] = None
    status_pembelian: Optional[str] = None
    keterangan_pembelian: Optional[str] = None


class PatientResponse(BaseModel):
    id: int
    facility_id: int
    nomor_rm: str
    nama: str
    nik: str
    tanggal_lahir: str
    jenis_kelamin: str
    telepon: str
    alamat: str
    alergi_obat: List[str]
    riwayat_penyakit: List[str]
    catatan_medis: str
    waktu_kunjungan: str
    penyakit_diderita: str
    status_pembelian: str
    keterangan_pembelian: str


def format_patient_response(p: Patient) -> dict:
    alergi_list = []
    if p.riwayat_alergi:
        try:
            alergi_list = json.loads(p.riwayat_alergi)
        except Exception:
            alergi_list = [s.strip() for s in p.riwayat_alergi.split(",") if s.strip()]

    riwayat_list = []
    if p.riwayat_komorbid:
        try:
            riwayat_list = json.loads(p.riwayat_komorbid)
        except Exception:
            riwayat_list = [s.strip() for s in p.riwayat_komorbid.split(",") if s.strip()]

    # Parse metadata tambahan yang dikemas dalam format JSON di catatan_medis jika ada
    catatan = p.catatan_medis or ""
    waktu_kunjungan = "2026-10-27 10:00"
    penyakit_diderita = "Pemeriksaan Rutin Apotek"
    status_pembelian = "Lunas"
    keterangan_pembelian = "Lunas Kasir"

    if catatan.startswith("{") and "metadata_kunjungan" in catatan:
        try:
            extra = json.loads(catatan)
            catatan = extra.get("catatan_klinis", "")
            waktu_kunjungan = extra.get("waktu_kunjungan", waktu_kunjungan)
            penyakit_diderita = extra.get("penyakit_diderita", penyakit_diderita)
            status_pembelian = extra.get("status_pembelian", status_pembelian)
            keterangan_pembelian = extra.get("keterangan_pembelian", keterangan_pembelian)
        except Exception:
            pass

    return {
        "id": p.id,
        "facility_id": p.facility_id,
        "nomor_rm": p.nomor_rm or f"RM-{p.id:04d}",
        "nama": p.nama_lengkap,
        "nik": p.nik or "-",
        "tanggal_lahir": str(p.tanggal_lahir) if p.tanggal_lahir else "1990-01-01",
        "jenis_kelamin": p.jenis_kelamin or "L",
        "telepon": p.no_hp or "-",
        "alamat": p.alamat or "-",
        "alergi_obat": alergi_list,
        "riwayat_penyakit": riwayat_list,
        "catatan_medis": catatan,
        "waktu_kunjungan": waktu_kunjungan,
        "penyakit_diderita": penyakit_diderita,
        "status_pembelian": status_pembelian,
        "keterangan_pembelian": keterangan_pembelian,
    }


# ==================== ENDPOINTS ====================
@router.get("", response_model=List[PatientResponse])
async def get_patients(
    search: Optional[str] = Query(None),
    facility_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Mengambil seluruh data pasien dari database (PostgreSQL / SQLite)."""
    stmt = select(Patient).order_by(desc(Patient.id))

    if facility_id:
        stmt = stmt.where(Patient.facility_id == facility_id)

    if search:
        search_pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Patient.nama_lengkap.ilike(search_pattern),
                Patient.nomor_rm.ilike(search_pattern),
                Patient.nik.ilike(search_pattern),
                Patient.no_hp.ilike(search_pattern),
                Patient.alamat.ilike(search_pattern)
            )
        )

    result = await db.execute(stmt)
    patients = result.scalars().all()
    return [format_patient_response(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_detail(patient_id: int, db: AsyncSession = Depends(get_db)):
    """Mengambil detail satu pasien berdasarkan ID."""
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Pasien tidak ditemukan di database.")
    return format_patient_response(patient)


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(req: PatientCreate, db: AsyncSession = Depends(get_db)):
    """Menambahkan data pasien baru ke database (PostgreSQL / SQLite)."""
    # Pastikan facility_id valid
    facility_id = req.facility_id
    if not facility_id:
        fac_stmt = select(Facility.id).limit(1)
        fac_res = await db.execute(fac_stmt)
        facility_id = fac_res.scalar_one_or_none() or 1

    # Format JSON untuk alergi dan riwayat komorbid
    alergi_json = json.dumps(req.alergi_obat or [])
    riwayat_json = json.dumps(req.riwayat_penyakit or [])

    # Format metadata catatan medis
    extra_meta = {
        "metadata_kunjungan": True,
        "catatan_klinis": req.catatan_medis or "",
        "waktu_kunjungan": req.waktu_kunjungan or datetime.now().strftime("%Y-%m-%d %H:%M"),
        "penyakit_diderita": req.penyakit_diderita or "Pemeriksaan Rutin Apotek",
        "status_pembelian": req.status_pembelian or "Lunas",
        "keterangan_pembelian": req.keterangan_pembelian or "Lunas Kasir"
    }

    tgl_lahir = None
    if req.tanggal_lahir:
        try:
            tgl_lahir = datetime.strptime(req.tanggal_lahir, "%Y-%m-%d").date()
        except Exception:
            pass

    new_patient = Patient(
        facility_id=facility_id,
        nomor_rm=req.nomor_rm or f"RM-{int(datetime.now().timestamp()) % 100000:05d}",
        nama_lengkap=req.nama_lengkap.strip(),
        nik=req.nik or "-",
        tanggal_lahir=tgl_lahir,
        jenis_kelamin=req.jenis_kelamin or "L",
        no_hp=req.no_hp or "-",
        alamat=req.alamat or "-",
        riwayat_alergi=alergi_json,
        riwayat_komorbid=riwayat_json,
        catatan_medis=json.dumps(extra_meta)
    )

    db.add(new_patient)
    await db.commit()
    await db.refresh(new_patient)

    return format_patient_response(new_patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: int, req: PatientUpdate, db: AsyncSession = Depends(get_db)):
    """Memperbarui data pasien yang sudah ada di database."""
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Pasien tidak ditemukan.")

    if req.nama_lengkap is not None:
        patient.nama_lengkap = req.nama_lengkap.strip()
    if req.nik is not None:
        patient.nik = req.nik
    if req.jenis_kelamin is not None:
        patient.jenis_kelamin = req.jenis_kelamin
    if req.no_hp is not None:
        patient.no_hp = req.no_hp
    if req.alamat is not None:
        patient.alamat = req.alamat
    if req.alergi_obat is not None:
        patient.riwayat_alergi = json.dumps(req.alergi_obat)
    if req.riwayat_penyakit is not None:
        patient.riwayat_komorbid = json.dumps(req.riwayat_penyakit)
    if req.tanggal_lahir is not None:
        try:
            patient.tanggal_lahir = datetime.strptime(req.tanggal_lahir, "%Y-%m-%d").date()
        except Exception:
            pass

    # Update metadata catatan & kunjungan
    extra_meta = {
        "metadata_kunjungan": True,
        "catatan_klinis": req.catatan_medis if req.catatan_medis is not None else "",
        "waktu_kunjungan": req.waktu_kunjungan or datetime.now().strftime("%Y-%m-%d %H:%M"),
        "penyakit_diderita": req.penyakit_diderita or "Pemeriksaan Rutin Apotek",
        "status_pembelian": req.status_pembelian or "Lunas",
        "keterangan_pembelian": req.keterangan_pembelian or "Lunas Kasir"
    }
    patient.catatan_medis = json.dumps(extra_meta)

    await db.commit()
    await db.refresh(patient)
    return format_patient_response(patient)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    """Menghapus data pasien dari database."""
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Pasien tidak ditemukan.")

    await db.delete(patient)
    await db.commit()
    return None
