from pydantic import BaseModel, EmailStr
from typing import Optional


class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    nama_lengkap: str
    role: Optional[str] = "ADMIN"  # ADMIN, APOTEKER, KASIR, KEUANGAN
    nama_faskes: Optional[str] = None
    tipe_faskes: Optional[str] = "Apotek Mandiri"
    nomor_izin_operasional: Optional[str] = None
    nomor_telepon: Optional[str] = None
    alamat_lengkap: Optional[str] = None
    kota: Optional[str] = None
    provinsi: Optional[str] = None
    foto_faskes_url: Optional[str] = None



class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    nama_lengkap: str
    role: str
    facility_id: int
    facility_name: str
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    is_shared_demo: bool = True
    demo_workspace_name: str = "Apotek Sehat Farma (Beta Demo)"


class UserUpdateRequest(BaseModel):
    nama_lengkap: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    facility_name: Optional[str] = None
    avatar_url: Optional[str] = None
