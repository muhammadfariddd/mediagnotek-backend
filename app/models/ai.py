from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class AIConsultationSession(Base):
    __tablename__ = "ai_consultation_sessions"

    id = Column(String(100), primary_key=True, index=True)  # Session UUID / Token
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    judul_konsultasi = Column(String(255), default="Konsultasi Telaah Resep & Diagnosa")
    mode_tampilan = Column(String(50), default="STANDARD")  # STANDARD, ROOM_CHAT_FULLSCREEN
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    facility = relationship("Facility", back_populates="ai_sessions")
    user = relationship("User", back_populates="ai_sessions")
    patient = relationship("Patient", back_populates="ai_sessions")
    messages = relationship("AIConsultationMessage", back_populates="session", cascade="all, delete-orphan")


class AIConsultationMessage(Base):
    __tablename__ = "ai_consultation_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("ai_consultation_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(String(20), nullable=False)  # USER, AI, SYSTEM
    content = Column(Text, nullable=False)
    lampiran_resep_url = Column(Text, nullable=True)
    detected_icd10_code = Column(String(20), nullable=True)
    detected_icd10_desc = Column(String(255), nullable=True)
    interaksi_ditemukan = Column(JSON, nullable=True)  # List of drug interactions found
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("AIConsultationSession", back_populates="messages")
