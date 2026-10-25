from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class StockMutation(Base):
    __tablename__ = "stock_mutations"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("drug_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    tipe_mutasi = Column(String(50), nullable=False)  # MASUK_FAKTUR, KELUAR_PENJUALAN, PENYESUAIAN_OPNAME, RETUR_PBF, RUSAK_KEDALUWARSA
    jumlah = Column(Integer, nullable=False)           # Positif jika masuk, negatif jika keluar
    stok_sebelum = Column(Integer, nullable=False)
    stok_sesudah = Column(Integer, nullable=False)
    referensi_id = Column(String(100), nullable=True, index=True)  # No struk kasir atau no faktur PBF
    keterangan = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    facility = relationship("Facility", back_populates="stock_mutations")
    drug = relationship("Drug")
    batch = relationship("DrugBatch", back_populates="mutations")


class CashFlow(Base):
    __tablename__ = "cash_flows"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    tanggal = Column(Date, nullable=False, index=True)
    tipe = Column(String(20), nullable=False)  # MASUK, KELUAR
    kategori = Column(String(100), nullable=False)  # PENJUALAN_KASIR, BAYAR_PBF, OPERASIONAL, GAJI, LAINNYA
    nominal = Column(Numeric(14, 2), nullable=False)
    deskripsi = Column(Text, nullable=True)
    referensi_transaksi_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    facility = relationship("Facility", back_populates="cash_flows")
    user = relationship("User", back_populates="cash_flows")
    transaction = relationship("Transaction")
