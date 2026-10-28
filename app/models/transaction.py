from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    nomor_struk = Column(String(100), unique=True, nullable=False, index=True)
    nama_kasir = Column(String(150), nullable=False, default="Kasir Apotek")
    nama_pasien = Column(String(200), nullable=False, default="Pasien Umum")
    dokter_perujuk = Column(String(200), nullable=True)
    tanggal_transaksi = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    jenis_transaksi = Column(String(50), nullable=False, default="BEBAS")
    total_omzet = Column(Numeric(14, 2), nullable=False, default=0)
    total_hpp = Column(Numeric(14, 2), nullable=False, default=0)
    laba_kotor = Column(Numeric(14, 2), nullable=False, default=0)
    margin_persen = Column(Numeric(6, 2), nullable=False, default=0)
    metode_bayar = Column(String(50), nullable=False, default="TUNAI")
    nominal_tunai = Column(Numeric(14, 2), nullable=True)
    nominal_kembalian = Column(Numeric(14, 2), nullable=True)
    catatan = Column(Text, nullable=True)

    facility = relationship("Facility", back_populates="transactions")
    cashier = relationship("User", back_populates="transactions")
    patient = relationship("Patient", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")


class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="SET NULL"), nullable=True, index=True)
    batch_id = Column(Integer, ForeignKey("drug_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    nama_obat = Column(String(255), nullable=False)
    jumlah = Column(Integer, nullable=False, default=1)
    satuan = Column(String(50), default="Tablet")
    harga_jual_satuan = Column(Numeric(12, 2), nullable=False, default=0)
    subtotal_omzet = Column(Numeric(14, 2), nullable=False, default=0)
    aturan_pakai = Column(String(200), nullable=True)

    transaction = relationship("Transaction", back_populates="items")
    batch = relationship("DrugBatch", back_populates="transaction_items")
