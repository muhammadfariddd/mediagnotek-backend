from pydantic import BaseModel
from typing import Optional


# --- Symptom ---

class SymptomOut(BaseModel):
    id: int
    nama: str
    model_config = {"from_attributes": True}


# --- Disease ---

class DiseaseBase(BaseModel):
    nama: str
    deskripsi: Optional[str] = None
    penyebab: Optional[str] = None
    gejala_teks: Optional[str] = None

class DiseaseListOut(BaseModel):
    id: int
    nama: str
    deskripsi: Optional[str] = None
    model_config = {"from_attributes": True}

class DiseaseDetailOut(DiseaseBase):
    id: int
    symptoms: list[SymptomOut] = []
    drugs: list["DrugListOut"] = []
    model_config = {"from_attributes": True}


# --- Drug ---

class DrugBase(BaseModel):
    nama: str
    deskripsi: Optional[str] = None
    peringatan: Optional[str] = None
    dosis: Optional[str] = None
    efek_samping: Optional[str] = None
    merek_dagang: Optional[str] = None

class DrugListOut(BaseModel):
    id: int
    nama: str
    deskripsi: Optional[str] = None
    merek_dagang: Optional[str] = None
    model_config = {"from_attributes": True}

class DrugDetailOut(DrugBase):
    id: int
    rxcui: Optional[str] = None
    diseases: list[DiseaseListOut] = []
    model_config = {"from_attributes": True}


# --- Diagnosis ---

class DiagnosisRequest(BaseModel):
    gejala: list[str]  # list nama gejala

class DiagnosisPrediction(BaseModel):
    penyakit: str
    confidence: float
    deskripsi: Optional[str] = None

class DiagnosisResponse(BaseModel):
    predictions: list[DiagnosisPrediction]
    obat_terkait: list[DrugListOut] = []


# --- Interaction ---

class InteractionCheckRequest(BaseModel):
    drug_ids: list[int]

class InteractionOut(BaseModel):
    drug1_nama: str
    drug2_nama: str
    severity: Optional[str] = None
    deskripsi: Optional[str] = None
    model_config = {"from_attributes": True}

class InteractionCheckResponse(BaseModel):
    has_interactions: bool
    interactions: list[InteractionOut] = []


# --- Stock ---

class StockPredictionOut(BaseModel):
    drug_id: int
    drug_nama: str
    tanggal: str
    stok_masuk: int
    stok_keluar: int
    sisa: int
    model_config = {"from_attributes": True}

class StockPredictRequest(BaseModel):
    drug_id: int
    period_days: int = 30


# --- Pagination ---

class PaginatedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: list
