from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    nomor_struk = Column(String(100), unique=True, nullable=False, index=True)  # TRX-YYYYMMDD-XXXX
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True)
    tanggal_transaksi = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    jenis_transaksi = Column(String(50), nullable=False, default="BEBAS")  # BEBAS, RESEP_PATEN, RESEP_RACIKAN
    total_omzet = Column(Numeric(14, 2), nullable=False, default=0)        # Total bayar dari pembeli
    total_hpp = Column(Numeric(14, 2), nullable=False, default=0)          # Total modal HPP batch
    laba_kotor = Column(Numeric(14, 2), nullable=False, default=0)         # total_omzet - total_hpp
    margin_persen = Column(Numeric(6, 2), nullable=False, default=0)       # (laba_kotor / total_omzet) * 100
    metode_bayar = Column(String(50), nullable=False, default="TUNAI")     # TUNAI, QRIS, DEBIT, TRANSFER
    nominal_tunai = Column(Numeric(14, 2), nullable=True)
    nominal_kembalian = Column(Numeric(14, 2), nullable=True)
    catatan = Column(Text, nullable=True)

    # Relationships
    facility = relationship("Facility", back_populates="transactions")
    cashier = relationship("User", back_populates="transactions")
    patient = relationship("Patient", back_populates="transactions")
    items = relationship("TransactionItem", back_populates="transaction", cascade="all, delete-orphan")


class TransactionItem(Base):
    __tablename__ = "transaction_items"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("drug_batches.id", ondelete="RESTRICT"), nullable=False, index=True)
    jumlah = Column(Integer, nullable=False)
    harga_jual_satuan = Column(Numeric(12, 2), nullable=False)  # Snapshot harga jual saat detik transaksi
    hpp_satuan = Column(Numeric(12, 2), nullable=False)         # Snapshot modal HPP batch saat detik transaksi
    subtotal_omzet = Column(Numeric(14, 2), nullable=False)     # jumlah * harga_jual_satuan
    subtotal_hpp = Column(Numeric(14, 2), nullable=False)       # jumlah * hpp_satuan
    laba_item = Column(Numeric(14, 2), nullable=False)          # subtotal_omzet - subtotal_hpp
    aturan_pakai = Column(String(200), nullable=True)           # misal: 3x1 sehari sesudah makan

    # Relationships
    transaction = relationship("Transaction", back_populates="items")
    drug = relationship("Drug")
    batch = relationship("DrugBatch", back_populates="transaction_items")
