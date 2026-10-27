import hashlib
import time
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.facility import Facility, User
from app.schemas.auth import (
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest
)

logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & User Management"])


def hash_password(password: str) -> str:
    """Hash password menggunakan SHA-256 + salt standar."""
    salt = "mediagnotek_secure_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def generate_jwt_token(user_id: int, email: str, role: str) -> str:
    """Buat token otentikasi sesi terverifikasi."""
    payload = f"uid:{user_id}|em:{email}|ro:{role}|ts:{int(time.time())}"
    sig = hashlib.sha256((payload + "mediagnotek_jwt_secret_key").encode("utf-8")).hexdigest()[:24]
    return f"mgt_{payload}_{sig}"


@router.post("/google", response_model=TokenResponse)
async def login_with_google(req: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Login / Signup dengan Google Account SSO.
    """
    if not req.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email Google tidak valid atau kosong."
        )

    email = req.email.strip().lower()
    nama = req.name or email.split("@")[0]
    avatar = req.picture or f"https://api.dicebear.com/7.x/initials/svg?seed={email}"

    logger.info(f"[SSO] Permintaan login Google untuk email: {email}")

    # Cari user berdasarkan email
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Buat Faskes baru untuk akun pendaftar Google ini
        nama_faskes = f"Faskes {nama}"
        new_facility = Facility(
            nama=nama_faskes,
            kode_faskes=f"FSK-{int(time.time()) % 100000}",
            alamat="Alamat belum disetel",
            email=email,
            nama_apa=nama,
            logo_url=avatar
        )
        db.add(new_facility)
        await db.commit()
        await db.refresh(new_facility)

        # Buat user baru
        username = email.split("@")[0].replace(".", "_") + f"_{int(time.time()) % 1000}"
        user = User(
            facility_id=new_facility.id,
            username=username,
            email=email,
            password_hash=hash_password(f"google_sso_{email}"),
            nama_lengkap=nama,
            role="ADMIN",
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info(f"[SSO] Akun Google baru berhasil didaftarkan: id={user.id}, email={email}")

    # Ambil data faskes user
    stmt_fac = select(Facility).where(Facility.id == user.facility_id)
    res_fac = await db.execute(stmt_fac)
    facility = res_fac.scalar_one_or_none()
    facility_name = facility.nama if facility else "Fasilitas Kesehatan"

    token = generate_jwt_token(user.id, user.email, user.role)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nama_lengkap=user.nama_lengkap,
            role=user.role,
            facility_id=user.facility_id,
            facility_name=facility_name,
            avatar_url=avatar
        ),
        is_shared_demo=False,
        demo_workspace_name=facility_name
    )


@router.post("/login", response_model=TokenResponse)
async def login_with_email(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login otentik dengan Email dan Password.
    Memverifikasi password hash asli di database.
    """
    req_email = req.email.strip().lower()
    logger.info(f"[LOGIN] Upaya login untuk email: {req_email}")

    stmt = select(User).where(User.email == req_email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"[LOGIN] Gagal: Email {req_email} tidak terdaftar di database.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau kata sandi tidak cocok. Silakan periksa kembali atau daftar akun baru."
        )

    # Validasi kesesuaian Password Hash
    expected_hash = hash_password(req.password)
    if user.password_hash != expected_hash:
        logger.warning(f"[LOGIN] Gagal: Kata sandi salah untuk email {req_email}.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email atau kata sandi tidak cocok. Silakan periksa kembali."
        )

    if not user.is_active:
        logger.warning(f"[LOGIN] Gagal: Akun {req_email} dalam status non-aktif.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun ini dinonaktifkan. Hubungi administrator."
        )

    # Ambil profil Faskes terkait
    stmt_fac = select(Facility).where(Facility.id == user.facility_id)
    res_fac = await db.execute(stmt_fac)
    facility = res_fac.scalar_one_or_none()
    facility_name = facility.nama if facility else "Fasilitas Kesehatan"

    token = generate_jwt_token(user.id, user.email, user.role)
    logger.info(f"[LOGIN] Sukses: User {user.username} ({user.email}) berhasil login. Faskes: {facility_name}")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nama_lengkap=user.nama_lengkap,
            role=user.role,
            facility_id=user.facility_id,
            facility_name=facility_name,
            avatar_url=None
        ),
        is_shared_demo=False,
        demo_workspace_name=facility_name
    )


@router.post("/register", response_model=TokenResponse)
async def register_account(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Pendaftaran akun dan fasilitas kesehatan (Faskes) baru resmi ke database.
    Membuat record Facility baru dan User Admin faskes baru.
    """
    req_email = req.email.strip().lower()
    logger.info(f"[REGISTER] Menerima pendaftaran faskes baru: {req.nama_faskes} ({req_email})")

    # 1. Cek apakah email sudah terdaftar
    stmt = select(User).where(User.email == req_email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        logger.warning(f"[REGISTER] Pendaftaran ditolak: Email {req_email} sudah digunakan.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ini sudah terdaftar. Silakan login menggunakan kata sandi Anda."
        )

    # 2. Buat entitas Fasilitas Kesehatan (Facility) baru
    faskes_name = (req.nama_faskes or "Apotek Baru").strip()
    alamat_lengkap = req.alamat_lengkap or "Belum disetel"
    if req.kota and req.provinsi:
        alamat_lengkap += f", {req.kota}, {req.provinsi}"

    new_facility = Facility(
        nama=faskes_name,
        kode_faskes=f"FSK-{int(time.time()) % 1000000}",
        alamat=alamat_lengkap,
        no_telp=req.nomor_telepon,
        email=req_email,
        nomor_sia=req.nomor_izin_operasional,
        nomor_sipa=req.nomor_izin_operasional,
        nama_apa=req.nama_lengkap,
        logo_url=req.foto_faskes_url
    )
    db.add(new_facility)
    await db.commit()
    await db.refresh(new_facility)
    logger.info(f"[REGISTER] Faskes baru tersimpan di database: id={new_facility.id}, nama='{new_facility.nama}'")

    # 3. Buat entitas Pengguna (User Admin Faskes)
    base_username = req_email.split("@")[0].replace(".", "_")
    username = f"{base_username}_{new_facility.id}"

    new_user = User(
        facility_id=new_facility.id,
        username=username,
        email=req_email,
        password_hash=hash_password(req.password),
        nama_lengkap=req.nama_lengkap.strip(),
        role=req.role or "ADMIN",
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    logger.info(f"[REGISTER] User admin berhasil dibuat: id={new_user.id}, email={new_user.email}, role={new_user.role}")

    token = generate_jwt_token(new_user.id, new_user.email, new_user.role)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            nama_lengkap=new_user.nama_lengkap,
            role=new_user.role,
            facility_id=new_facility.id,
            facility_name=new_facility.nama,
            avatar_url=req.foto_faskes_url
        ),
        is_shared_demo=False,
        demo_workspace_name=new_facility.nama
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Mendapatkan profil akun yang sedang login dari database."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi login tidak teridentifikasi. Harap sertakan user_id atau login ulang."
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengguna tidak ditemukan di database."
        )

    stmt_fac = select(Facility).where(Facility.id == user.facility_id)
    res_fac = await db.execute(stmt_fac)
    facility = res_fac.scalar_one_or_none()
    facility_name = facility.nama if facility else "Fasilitas Kesehatan"


    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nama_lengkap=user.nama_lengkap,
        role=user.role,
        facility_id=user.facility_id,
        facility_name=facility_name,
        avatar_url=None
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    req: UserUpdateRequest,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Memperbarui profil akun user dan faskes secara dinamis dan menyimpannya di database."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID diperlukan untuk memperbarui profil."
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pengguna tidak ditemukan."
        )

    if req.nama_lengkap:
        user.nama_lengkap = req.nama_lengkap
    if req.email:
        user.email = req.email
    if req.role:
        user.role = req.role

    stmt_fac = select(Facility).where(Facility.id == user.facility_id)
    res_fac = await db.execute(stmt_fac)
    facility = res_fac.scalar_one_or_none()

    if facility and req.facility_name:
        facility.nama = req.facility_name

    await db.commit()
    await db.refresh(user)
    if facility:
        await db.refresh(facility)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nama_lengkap=user.nama_lengkap,
        role=user.role,
        facility_id=user.facility_id,
        facility_name=facility.nama if facility else "Fasilitas Kesehatan",
        avatar_url=req.avatar_url
    )


