from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    nama_pbf = Column(String(255), nullable=False, index=True)
    no_izin_pbf = Column(String(100), nullable=True)
    nama_kontak = Column(String(150), nullable=True)
    no_telp = Column(String(50), nullable=True)
    alamat = Column(Text, nullable=True)
    nomor_rekening = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    invoices = relationship("PurchaseInvoice", back_populates="supplier")
    batches = relationship("DrugBatch", back_populates="supplier")


class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    nomor_faktur = Column(String(100), nullable=False, index=True)
    tanggal_faktur = Column(Date, nullable=False)
    jatuh_tempo = Column(Date, nullable=True)
    total_bruto = Column(Numeric(14, 2), nullable=False, default=0)
    diskon_nominal = Column(Numeric(14, 2), nullable=False, default=0)
    ppn_nominal = Column(Numeric(14, 2), nullable=False, default=0)
    total_neto = Column(Numeric(14, 2), nullable=False, default=0)
    status_pembayaran = Column(String(50), nullable=False, default="LUNAS")  # LUNAS, HUTANG, KONSINYASI
    bukti_faktur_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    supplier = relationship("Supplier", back_populates="invoices")
    items = relationship("PurchaseInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")


class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="RESTRICT"), nullable=False)
    batch_id = Column(Integer, ForeignKey("drug_batches.id", ondelete="SET NULL"), nullable=True)
    jumlah = Column(Integer, nullable=False)
    harga_satuan_hpp = Column(Numeric(12, 2), nullable=False)
    diskon_persen = Column(Numeric(5, 2), default=0)
    subtotal = Column(Numeric(14, 2), nullable=False)

    # Relationships
    invoice = relationship("PurchaseInvoice", back_populates="items")
    drug = relationship("Drug")
    batch = relationship("DrugBatch")
