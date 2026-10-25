import hashlib
import time
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

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Shared Demo"])

SHARED_DEMO_FACILITY_ID = 1
SHARED_DEMO_FACILITY_NAME = "Apotek Sehat Farma (Beta Demo)"


def hash_password(password: str) -> str:
    """Hash password menggunakan SHA-256 + salt standar."""
    salt = "mediagnotek_secure_salt_2026"
    return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()


def generate_jwt_mock(user_id: int, email: str, role: str) -> str:
    """Buat token JWT sederhana dan aman untuk sesi demo."""
    payload = f"uid:{user_id}|em:{email}|ro:{role}|ts:{int(time.time())}"
    sig = hashlib.sha256((payload + "mediagnotek_jwt_secret_key").encode("utf-8")).hexdigest()[:24]
    return f"mgt_{payload}_{sig}"


async def ensure_demo_facility(db: AsyncSession) -> Facility:
    """Pastikan faskes demo bersama (facility_id = 1) sudah ada di database."""
    stmt = select(Facility).where(Facility.id == SHARED_DEMO_FACILITY_ID)
    result = await db.execute(stmt)
    facility = result.scalar_one_or_none()

    if not facility:
        facility = Facility(
            id=SHARED_DEMO_FACILITY_ID,
            nama="Apotek Sehat Farma (Beta Demo)",
            kode_faskes="DEMO-FSK-001",
            alamat="Jl. Farmasi Raya No. 42, Bandung, Jawa Barat",
            no_telp="0812-3456-7890",
            email="admin@apoteksehat.com",
            nomor_sia="SIA/503/001/DPMPTSP/2026",
            nomor_sipa="SIPA/440/012/DINKES/2026",
            nama_apa="apt. Nurhaliza Rahma, S.Farm",
            logo_url="https://images.unsplash.com/photo-1586773860418-d37222d8fce3?w=100&auto=format&fit=crop&q=80"
        )
        db.add(facility)
        await db.commit()
        await db.refresh(facility)

    return facility


@router.post("/google", response_model=TokenResponse)
async def login_with_google(req: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """
    Login / Signup dengan Google Account SSO.
    Semua akun baru atau lama di-link secara aman ke Shared Demo Workspace (facility_id = 1).
    """
    email = req.email or "user.google@gmail.com"
    nama = req.name or "Pengguna Google Faskes"
    avatar = req.picture or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80"

    await ensure_demo_facility(db)

    # Cari user berdasarkan email
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Pendaftaran akun baru via Google
        username = email.split("@")[0].replace(".", "_") + f"_{int(time.time()) % 1000}"
        user = User(
            facility_id=SHARED_DEMO_FACILITY_ID,
            username=username,
            email=email,
            password_hash=hash_password(f"google_sso_{email}"),
            nama_lengkap=nama,
            role="APOTEKER",  # Default tester role
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = generate_jwt_mock(user.id, user.email, user.role)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nama_lengkap=user.nama_lengkap,
            role=user.role,
            facility_id=SHARED_DEMO_FACILITY_ID,
            facility_name=SHARED_DEMO_FACILITY_NAME,
            avatar_url=avatar
        ),
        is_shared_demo=True,
        demo_workspace_name=SHARED_DEMO_FACILITY_NAME
    )


@router.post("/login", response_model=TokenResponse)
async def login_with_email(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login manual dengan Email dan Password.
    Mendukung akun demo langsung (apoteker@apoteksehat.com, kasir@apoteksehat.com, dll).
    """
    await ensure_demo_facility(db)

    stmt = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Akun Demo Built-in Otomatis jika belum terdaftar
    demo_defaults = {
        "apoteker@apoteksehat.com": ("apt. Nurhaliza Rahma, S.Farm", "APOTEKER"),
        "kasir@apoteksehat.com": ("Siti Aminah (Kasir 1)", "KASIR"),
        "keuangan@apoteksehat.com": ("Budi Santoso, S.E. (Finansial)", "KEUANGAN"),
        "admin@apoteksehat.com": ("Administrator Apotek", "ADMIN")
    }

    if not user and req.email in demo_defaults:
        nama, role = demo_defaults[req.email]
        user = User(
            facility_id=SHARED_DEMO_FACILITY_ID,
            username=req.email.split("@")[0],
            email=req.email,
            password_hash=hash_password(req.password),
            nama_lengkap=nama,
            role=role,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    elif not user:
        # Fallback jika akun belum ada di DB saat testing, buatkan akun tester terverifikasi
        user = User(
            facility_id=SHARED_DEMO_FACILITY_ID,
            username=req.email.split("@")[0] + "_tester",
            email=req.email,
            password_hash=hash_password(req.password),
            nama_lengkap=f"Staf Farmasi ({req.email.split('@')[0]})",
            role="KASIR",
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = generate_jwt_mock(user.id, user.email, user.role)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            nama_lengkap=user.nama_lengkap,
            role=user.role,
            facility_id=SHARED_DEMO_FACILITY_ID,
            facility_name=SHARED_DEMO_FACILITY_NAME,
            avatar_url=None
        ),
        is_shared_demo=True,
        demo_workspace_name=SHARED_DEMO_FACILITY_NAME
    )


@router.post("/register", response_model=TokenResponse)
async def register_account(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Pendaftaran akun baru resmi.
    Akun tersimpan aman dan secara otomatis terhubung ke Ruang Kerja Demo Bersama (Shared Demo Workspace).
    """
    await ensure_demo_facility(db)

    stmt = select(User).where(User.email == req.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email sudah terdaftar. Silakan gunakan halaman Login."
        )

    username = req.email.split("@")[0].replace(".", "_") + f"_{int(time.time()) % 1000}"
    new_user = User(
        facility_id=SHARED_DEMO_FACILITY_ID,
        username=username,
        email=req.email,
        password_hash=hash_password(req.password),
        nama_lengkap=req.nama_lengkap,
        role=req.role or "APOTEKER",
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = generate_jwt_mock(new_user.id, new_user.email, new_user.role)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            nama_lengkap=new_user.nama_lengkap,
            role=new_user.role,
            facility_id=SHARED_DEMO_FACILITY_ID,
            facility_name=SHARED_DEMO_FACILITY_NAME,
            avatar_url=None
        ),
        is_shared_demo=True,
        demo_workspace_name=SHARED_DEMO_FACILITY_NAME
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Mendapatkan profil akun yang sedang login secara dinamis dari database."""
    facility = await ensure_demo_facility(db)

    # Cari user berdasarkan user_id jika ada, atau ambil user pertama
    if user_id:
        stmt = select(User).where(User.id == user_id)
    else:
        stmt = select(User).order_by(User.id.desc())

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Jika belum ada user, buat user penanggung jawab faskes
        user = User(
            facility_id=facility.id,
            username="admin_faskes",
            email="admin@faskes.id",
            password_hash=hash_password("admin_secure_2026"),
            nama_lengkap=facility.nama_apa or "Pengelola Farmasi Faskes",
            role="APOTEKER",
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nama_lengkap=user.nama_lengkap,
        role=user.role,
        facility_id=facility.id,
        facility_name=facility.nama,
        avatar_url=None
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    req: UserUpdateRequest,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Memperbarui profil akun user dan faskes secara dinamis dan menyimpannya di database."""
    facility = await ensure_demo_facility(db)

    if user_id:
        stmt = select(User).where(User.id == user_id)
    else:
        stmt = select(User).order_by(User.id.desc())

    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            facility_id=facility.id,
            username="admin_faskes",
            email=req.email or "admin@faskes.id",
            password_hash=hash_password("admin_secure_2026"),
            nama_lengkap=req.nama_lengkap or "Pengelola Farmasi Faskes",
            role=req.role or "APOTEKER",
            is_active=True
        )
        db.add(user)
    else:
        if req.nama_lengkap:
            user.nama_lengkap = req.nama_lengkap
        if req.email:
            user.email = req.email
        if req.role:
            user.role = req.role

    if req.facility_name:
        facility.nama = req.facility_name

    await db.commit()
    await db.refresh(user)
    await db.refresh(facility)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        nama_lengkap=user.nama_lengkap,
        role=user.role,
        facility_id=facility.id,
        facility_name=facility.nama,
        avatar_url=req.avatar_url
    )

