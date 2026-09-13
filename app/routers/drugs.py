from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models import Drug, DrugInteraction
from app.schemas import DrugListOut, DrugDetailOut, InteractionOut, PaginatedResponse

router = APIRouter(prefix="/api/v1/drugs", tags=["Drugs"])


@router.get("", response_model=PaginatedResponse)
async def list_drugs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str = Query(None, description="Cari berdasarkan nama obat"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Drug)
    count_query = select(func.count(Drug.id))

    if search:
        query = query.where(Drug.nama.ilike(f"%{search}%"))
        count_query = count_query.where(Drug.nama.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar()

    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    drugs = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        size=size,
        items=[DrugListOut.model_validate(d) for d in drugs],
    )


@router.get("/{drug_id}", response_model=DrugDetailOut)
async def get_drug(drug_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Drug)
        .options(selectinload(Drug.diseases))
        .where(Drug.id == drug_id)
    )
    result = await db.execute(query)
    drug = result.scalar_one_or_none()
    if not drug:
        raise HTTPException(status_code=404, detail="Obat tidak ditemukan")
    return DrugDetailOut.model_validate(drug)


@router.get("/{drug_id}/interactions", response_model=list[InteractionOut])
async def get_drug_interactions(drug_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(DrugInteraction)
        .where(
            (DrugInteraction.drug_id_1 == drug_id) | (DrugInteraction.drug_id_2 == drug_id)
        )
        .options(
            selectinload(DrugInteraction.drug1),
            selectinload(DrugInteraction.drug2),
        )
    )
    result = await db.execute(query)
    interactions = result.scalars().all()

    return [
        InteractionOut(
            drug1_nama=i.drug1.nama,
            drug2_nama=i.drug2.nama,
            severity=i.severity,
            deskripsi=i.deskripsi,
        )
        for i in interactions
    ]
