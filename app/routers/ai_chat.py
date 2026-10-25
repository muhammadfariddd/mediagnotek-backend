from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.services.ai_service import process_ai_chat

router = APIRouter(prefix="/api/v1/ai", tags=["AI Clinical Assistant"])


class AIChatRequest(BaseModel):
    message: str
    patient_context: Optional[Dict[str, Any]] = None
    attachment: Optional[Dict[str, Any]] = None
    api_key: Optional[str] = None
    facility_id: Optional[int] = 1


class AIChatResponse(BaseModel):
    reply: str
    icd_code: str
    confidence: str
    provider: str
    timestamp: str


@router.post("/chat", response_model=AIChatResponse)
async def chat_with_clinical_ai(req: AIChatRequest):
    """
    Endpoint Konsultasi AI Klinis & Apoteker.
    Menerima pesan, konteks pasien, dan berkas/gambar lampiran,
    lalu menghasilkan analisis medis, estimasi ICD-10, dan tingkat keyakinan (confidence).
    """
    if not req.message.strip() and not req.attachment:
        raise HTTPException(status_code=400, detail="Pesan atau lampiran tidak boleh kosong.")

    result = await process_ai_chat(
        message=req.message,
        client_api_key=req.api_key,
        attachment=req.attachment,
        patient_context=req.patient_context
    )

    now_str = datetime.now().strftime("%H:%M WIB")

    return AIChatResponse(
        reply=result["text"],
        icd_code=result.get("icd_code", "ICD-10 Evaluasi"),
        confidence=result.get("confidence", "95.0%"),
        provider=result.get("provider", "MediagnoTek AI Engine"),
        timestamp=now_str
    )
