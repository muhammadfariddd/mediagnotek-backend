from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models import Drug, DrugInteraction
from app.schemas import InteractionCheckRequest, InteractionCheckResponse, InteractionOut
from app.services.rxnav_service import check_rxnav_interactions

router = APIRouter(prefix="/api/v1/interactions", tags=["Interactions"])


@router.post("/check", response_model=InteractionCheckResponse)
async def check_interactions(
    req: InteractionCheckRequest, db: AsyncSession = Depends(get_db)
):
    """
    Cek interaksi antar beberapa obat.
    1. Cek di database lokal dulu (cache).
    2. Jika tidak ada, panggil RxNav API lalu simpan hasilnya.
    """
    if len(req.drug_ids) < 2:
        raise HTTPException(status_code=400, detail="Minimal 2 obat untuk cek interaksi")

    # Ambil data obat
    query = select(Drug).where(Drug.id.in_(req.drug_ids))
    result = await db.execute(query)
    drugs = result.scalars().all()

    if len(drugs) < 2:
        raise HTTPException(status_code=404, detail="Obat tidak ditemukan")

    # Cek interaksi di database lokal
    interactions = []
    drug_ids = [d.id for d in drugs]

    for i in range(len(drug_ids)):
        for j in range(i + 1, len(drug_ids)):
            d1, d2 = drug_ids[i], drug_ids[j]
            query = select(DrugInteraction).where(
                ((DrugInteraction.drug_id_1 == d1) & (DrugInteraction.drug_id_2 == d2))
                | ((DrugInteraction.drug_id_1 == d2) & (DrugInteraction.drug_id_2 == d1))
            ).options(
                selectinload(DrugInteraction.drug1),
                selectinload(DrugInteraction.drug2),
            )
            result = await db.execute(query)
            found = result.scalars().all()
            interactions.extend(found)

    # Jika tidak ditemukan di lokal, coba RxNav
    if not interactions:
        rxcui_list = [d.rxcui for d in drugs if d.rxcui]
        if len(rxcui_list) >= 2:
            rxnav_results = await check_rxnav_interactions(rxcui_list)
            # Simpan hasil ke database
            for r in rxnav_results:
                new_interaction = DrugInteraction(
                    drug_id_1=r["drug_id_1"],
                    drug_id_2=r["drug_id_2"],
                    severity=r.get("severity"),
                    deskripsi=r.get("deskripsi"),
                )
                db.add(new_interaction)
            await db.commit()

            # Reload
            for i in range(len(drug_ids)):
                for j in range(i + 1, len(drug_ids)):
                    d1, d2 = drug_ids[i], drug_ids[j]
                    query = select(DrugInteraction).where(
                        ((DrugInteraction.drug_id_1 == d1) & (DrugInteraction.drug_id_2 == d2))
                        | ((DrugInteraction.drug_id_1 == d2) & (DrugInteraction.drug_id_2 == d1))
                    ).options(
                        selectinload(DrugInteraction.drug1),
                        selectinload(DrugInteraction.drug2),
                    )
                    result = await db.execute(query)
                    found = result.scalars().all()
                    interactions.extend(found)

    interaction_list = [
        InteractionOut(
            drug1_nama=i.drug1.nama,
            drug2_nama=i.drug2.nama,
            severity=i.severity,
            deskripsi=i.deskripsi,
        )
        for i in interactions
    ]

    return InteractionCheckResponse(
        has_interactions=len(interaction_list) > 0,
        interactions=interaction_list,
    )
