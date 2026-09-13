from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.database import Base

# --- Association Tables ---

disease_drug = Table(
    "disease_drug",
    Base.metadata,
    Column("disease_id", Integer, ForeignKey("diseases.id"), primary_key=True),
    Column("drug_id", Integer, ForeignKey("drugs.id"), primary_key=True),
)

disease_symptom = Table(
    "disease_symptom",
    Base.metadata,
    Column("disease_id", Integer, ForeignKey("diseases.id"), primary_key=True),
    Column("symptom_id", Integer, ForeignKey("symptoms.id"), primary_key=True),
)


# --- Models ---

class Disease(Base):
    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(500), nullable=False, index=True)
    deskripsi = Column(Text)
    penyebab = Column(Text)
    gejala_teks = Column(Text)  # teks asli dari CSV

    # relationships
    drugs = relationship("Drug", secondary=disease_drug, back_populates="diseases")
    symptoms = relationship("Symptom", secondary=disease_symptom, back_populates="diseases")


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(500), nullable=False, index=True)
    deskripsi = Column(Text)
    peringatan = Column(Text)
    dosis = Column(Text)
    efek_samping = Column(Text)
    merek_dagang = Column(String(1000))
    rxcui = Column(String(50), nullable=True, index=True)  # mapping RxNav

    # relationships
    diseases = relationship("Disease", secondary=disease_drug, back_populates="drugs")
    interactions_as_drug1 = relationship(
        "DrugInteraction", foreign_keys="DrugInteraction.drug_id_1", back_populates="drug1"
    )
    interactions_as_drug2 = relationship(
        "DrugInteraction", foreign_keys="DrugInteraction.drug_id_2", back_populates="drug2"
    )


class Symptom(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    nama = Column(String(300), nullable=False, unique=True, index=True)

    # relationships
    diseases = relationship("Disease", secondary=disease_symptom, back_populates="symptoms")


class DrugInteraction(Base):
    __tablename__ = "drug_interactions"

    id = Column(Integer, primary_key=True, index=True)
    drug_id_1 = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    drug_id_2 = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    severity = Column(String(50))  # low, moderate, high
    deskripsi = Column(Text)

    # relationships
    drug1 = relationship("Drug", foreign_keys=[drug_id_1])
    drug2 = relationship("Drug", foreign_keys=[drug_id_2])


class StockPrediction(Base):
    __tablename__ = "stock_predictions"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    tanggal = Column(String(10), nullable=False)  # YYYY-MM-DD
    stok_masuk = Column(Integer, default=0)
    stok_keluar = Column(Integer, default=0)
    sisa = Column(Integer, default=0)

    # relationships
    drug = relationship("Drug")
