from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models import Disease, disease_symptom, Symptom
from app.schemas import DiagnosisRequest, DiagnosisResponse, DiagnosisPrediction, DrugListOut

router = APIRouter(prefix="/api/v1/diagnosis", tags=["Diagnosis"])


@router.post("", response_model=DiagnosisResponse)
async def diagnose(req: DiagnosisRequest, db: AsyncSession = Depends(get_db)):
    """
    Menerima daftar gejala, mengembalikan prediksi penyakit.

    Strategi saat ini: text-matching (cocokkan gejala input dengan
    tabel symptoms, hitung penyakit yang paling banyak cocok).
    Bisa diganti dengan model ML/deep learning nanti.
    """
    gejala_input = [g.lower().strip() for g in req.gejala]

    # Cari symptom yang cocok
    symptom_query = select(Symptom).where(
        Symptom.nama.in_(gejala_input)
    )
    result = await db.execute(symptom_query)
    matched_symptoms = result.scalars().all()
    matched_ids = [s.id for s in matched_symptoms]

    if not matched_ids:
        return DiagnosisResponse(predictions=[], obat_terkait=[])

    # Hitung penyakit berdasarkan jumlah gejala yang cocok
    from sqlalchemy import func

    disease_scores = (
        select(
            disease_symptom.c.disease_id,
            func.count(disease_symptom.c.symptom_id).label("score"),
        )
        .where(disease_symptom.c.symptom_id.in_(matched_ids))
        .group_by(disease_symptom.c.disease_id)
        .order_by(func.count(disease_symptom.c.symptom_id).desc())
        .limit(5)
    )
    score_result = await db.execute(disease_scores)
    scores = score_result.all()

    if not scores:
        return DiagnosisResponse(predictions=[], obat_terkait=[])

    max_score = scores[0].score
    predictions = []
    all_disease_ids = []

    for row in scores:
        disease = await db.execute(
            select(Disease).where(Disease.id == row.disease_id)
        )
        d = disease.scalar_one_or_none()
        if d:
            confidence = round(row.score / len(gejala_input), 2)
            predictions.append(
                DiagnosisPrediction(
                    penyakit=d.nama,
                    confidence=min(confidence, 1.0),
                    deskripsi=d.deskripsi,
                )
            )
            all_disease_ids.append(d.id)

    # Ambil obat terkait dari penyakit teratas
    top_disease_id = all_disease_ids[0] if all_disease_ids else None
    obat_terkait = []
    if top_disease_id:
        disease_with_drugs = await db.execute(
            select(Disease)
            .options(selectinload(Disease.drugs))
            .where(Disease.id == top_disease_id)
        )
        d = disease_with_drugs.scalar_one_or_none()
        if d and d.drugs:
            obat_terkait = [DrugListOut.model_validate(drug) for drug in d.drugs]

    return DiagnosisResponse(predictions=predictions, obat_terkait=obat_terkait)
