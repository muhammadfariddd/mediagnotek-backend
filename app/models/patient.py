from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    nomor_rm = Column(String(50), nullable=False, index=True)  # No Rekam Medis Farmasi
    nama_lengkap = Column(String(200), nullable=False, index=True)
    nik = Column(String(20), nullable=True, index=True)
    tanggal_lahir = Column(Date, nullable=True)
    jenis_kelamin = Column(String(10), nullable=True)  # L, P
    no_hp = Column(String(30), nullable=False, index=True)
    alamat = Column(Text, nullable=True)
    riwayat_alergi = Column(Text, nullable=True)    # Contoh: Alergi Amoksisilin, NSAID
    riwayat_komorbid = Column(Text, nullable=True)  # Contoh: Hipertensi, Diabetes Melitus
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    facility = relationship("Facility", back_populates="patients")
    transactions = relationship("Transaction", back_populates="patient")
    ai_sessions = relationship("AIConsultationSession", back_populates="patient")
