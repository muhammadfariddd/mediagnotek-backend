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
    role: Optional[str] = "KASIR"  # ADMIN, APOTEKER, KASIR, KEUANGAN


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
