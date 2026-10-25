from sqlalchemy import Column, Integer, String, Text, Numeric, Date, Boolean, DateTime, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from app.db.database import Base

# Association Tables
disease_drug = Table(
    "disease_drug",
    Base.metadata,
    Column("disease_id", Integer, ForeignKey("diseases.id", ondelete="CASCADE"), primary_key=True),
    Column("drug_id", Integer, ForeignKey("drugs.id", ondelete="CASCADE"), primary_key=True),
)

disease_symptom = Table(
    "disease_symptom",
    Base.metadata,
    Column("disease_id", Integer, ForeignKey("diseases.id", ondelete="CASCADE"), primary_key=True),
    Column("symptom_id", Integer, ForeignKey("symptoms.id", ondelete="CASCADE"), primary_key=True),
)


class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(500), nullable=False, index=True)
    deskripsi = Column(Text, nullable=True)
    penyebab = Column(Text, nullable=True)
    gejala_teks = Column(Text, nullable=True)

    # Relationships
    drugs = relationship("Drug", secondary=disease_drug, back_populates="diseases")
    symptoms = relationship("Symptom", secondary=disease_symptom, back_populates="diseases")


class Symptom(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(300), nullable=False, unique=True, index=True)

    # Relationships
    diseases = relationship("Disease", secondary=disease_symptom, back_populates="symptoms")


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(500), nullable=False, index=True)
    deskripsi = Column(Text, nullable=True)
    peringatan = Column(Text, nullable=True)
    dosis = Column(Text, nullable=True)
    efek_samping = Column(Text, nullable=True)
    merek_dagang = Column(String(1000), nullable=True)
    rxcui = Column(String(50), nullable=True, index=True)  # mapping RxNav

    # Enhanced Pharmacy Fields
    barcode = Column(String(100), unique=True, nullable=True, index=True)
    satuan_terkecil = Column(String(50), nullable=False, default="Tablet")  # Tablet, Strip, Botol, Vial, Ampul
    golongan = Column(String(50), nullable=False, default="Bebas")           # Bebas, Bebas Terbatas, Keras, Narkotika, Psikotropika
    stok_minimum = Column(Integer, nullable=False, default=10)
    harga_jual_default = Column(Numeric(12, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    diseases = relationship("Disease", secondary=disease_drug, back_populates="drugs")
    batches = relationship("DrugBatch", back_populates="drug", cascade="all, delete-orphan")
    interactions_as_drug1 = relationship(
        "DrugInteraction", foreign_keys="DrugInteraction.drug_id_1", back_populates="drug1"
    )
    interactions_as_drug2 = relationship(
        "DrugInteraction", foreign_keys="DrugInteraction.drug_id_2", back_populates="drug2"
    )


class DrugBatch(Base):
    __tablename__ = "drug_batches"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True)
    batch_number = Column(String(100), nullable=False, index=True)
    expired_date = Column(Date, nullable=False, index=True)  # Core of FEFO ordering
    stok_awal = Column(Integer, nullable=False, default=0)
    stok_sisa = Column(Integer, nullable=False, default=0)
    harga_beli_hpp = Column(Numeric(12, 2), nullable=False)  # HPP Modal per unit
    harga_jual = Column(Numeric(12, 2), nullable=False)      # Consumer selling price
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    facility = relationship("Facility", back_populates="drug_batches")
    drug = relationship("Drug", back_populates="batches")
    supplier = relationship("Supplier", back_populates="batches")
    mutations = relationship("StockMutation", back_populates="batch")
    transaction_items = relationship("TransactionItem", back_populates="batch")


class DrugInteraction(Base):
    __tablename__ = "drug_interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug_id_1 = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    drug_id_2 = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    severity = Column(String(50), nullable=True)  # low, moderate, high
    deskripsi = Column(Text, nullable=True)

    # Relationships
    drug1 = relationship("Drug", foreign_keys=[drug_id_1])
    drug2 = relationship("Drug", foreign_keys=[drug_id_2])


class StockPrediction(Base):
    __tablename__ = "stock_predictions"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    tanggal = Column(String(10), nullable=False)  # YYYY-MM-DD
    stok_masuk = Column(Integer, default=0)
    stok_keluar = Column(Integer, default=0)
    sisa = Column(Integer, default=0)

    # Relationships
    drug = relationship("Drug")
