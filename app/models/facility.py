from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(255), nullable=False, index=True)
    kode_faskes = Column(String(50), unique=True, index=True, nullable=True)
    alamat = Column(Text, nullable=False)
    no_telp = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    nomor_sia = Column(String(100), nullable=True)   # Surat Izin Apotek
    nomor_sipa = Column(String(100), nullable=True)  # SIPA Apoteker Pengelola (APA)
    nama_apa = Column(String(200), nullable=True)    # Nama Apoteker Pengelola Apotek
    logo_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="facility", cascade="all, delete-orphan")
    drug_batches = relationship("DrugBatch", back_populates="facility")
    patients = relationship("Patient", back_populates="facility")
    transactions = relationship("Transaction", back_populates="facility")
    stock_mutations = relationship("StockMutation", back_populates="facility")
    cash_flows = relationship("CashFlow", back_populates="facility")
    ai_sessions = relationship("AIConsultationSession", back_populates="facility")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nama_lengkap = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False, default="KASIR")  # ADMIN, APOTEKER, KASIR, KEUANGAN
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    facility = relationship("Facility", back_populates="users")
    transactions = relationship("Transaction", back_populates="cashier")
    cash_flows = relationship("CashFlow", back_populates="user")
    ai_sessions = relationship("AIConsultationSession", back_populates="user")
