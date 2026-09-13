from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models import Disease
from app.schemas import DiseaseListOut, DiseaseDetailOut, PaginatedResponse

router = APIRouter(prefix="/api/v1/diseases", tags=["Diseases"])


@router.get("", response_model=PaginatedResponse)
async def list_diseases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str = Query(None, description="Cari berdasarkan nama penyakit"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Disease)
    count_query = select(func.count(Disease.id))

    if search:
        query = query.where(Disease.nama.ilike(f"%{search}%"))
        count_query = count_query.where(Disease.nama.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar()

    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    diseases = result.scalars().all()

    return PaginatedResponse(
        total=total,
        page=page,
        size=size,
        items=[DiseaseListOut.model_validate(d) for d in diseases],
    )


@router.get("/{disease_id}", response_model=DiseaseDetailOut)
async def get_disease(disease_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Disease)
        .options(selectinload(Disease.symptoms), selectinload(Disease.drugs))
        .where(Disease.id == disease_id)
    )
    result = await db.execute(query)
    disease = result.scalar_one_or_none()
    if not disease:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Penyakit tidak ditemukan")
    return DiseaseDetailOut.model_validate(disease)
