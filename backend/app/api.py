from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import PlainTextResponse
from typing import Optional, List
import uuid
import logging

from app.services.extract_text import extract_text_from_file
from app.services.analyze import analyze_cv
from app.services.llm import llm_compare_cvs, llm_canonicalize, llm_keyword_matching
from app.services.scoring import fallback_scoring_if_needed
from app.models.cv import CvAnalysisResponse, CVComparisonResult

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze-cv", response_model=CvAnalysisResponse)
def analyze_cv_endpoint(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
):
    allowed = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }

    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Format non supporté. PDF ou DOCX uniquement.")

    raw_bytes = file.file.read()

    try:
        cv_text, warnings = extract_text_from_file(raw_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur extraction: {e}")

    result = analyze_cv(
        cv_text=cv_text,
        extraction_warnings=warnings,
        job_description=job_description,
    )
    return result


@router.post("/debug/extract-text", response_class=PlainTextResponse)
def debug_extract_text(file: UploadFile = File(...)):
    raw_bytes = file.file.read()
    cv_text, _warnings = extract_text_from_file(raw_bytes, file.filename)
    return cv_text


@router.post("/compare-cvs", response_model=CVComparisonResult)
def compare_cvs_endpoint(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...),
):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Au moins 2 CV sont nécessaires pour une comparaison.")

    allowed = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }

    cvs_data = []

    for file in files:
        if file.content_type not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Format non supporté pour {file.filename}. PDF ou DOCX uniquement.",
            )

        raw_bytes = file.file.read()

        try:
            cv_text, warnings = extract_text_from_file(raw_bytes, file.filename)
            canonical = llm_canonicalize(cv_text, warnings)
            canonical = fallback_scoring_if_needed(canonical)

            cv_id = str(uuid.uuid4())[:8]
            cvs_data.append((cv_id, file.filename, canonical))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur extraction pour {file.filename}: {e}",
            )

    try:
        result = llm_compare_cvs(cvs_data, job_description)

        # Enrichir chaque CV avec le matching mots-clés
        for cv_item in result.cvs:
            try:
                keyword_matching = llm_keyword_matching(cv_item.canonical, job_description)
                cv_item.keyword_matching = keyword_matching
            except Exception as e:
                logger.warning(
                    f"Erreur analyse mots-clés pour {cv_item.filename}: {e}"
                )

        return result

    except Exception as e:
        logger.error("Erreur lors de la comparaison", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison: {str(e)}")


@router.get("/debug/config")
def debug_config():
    from app.core.config import settings
    from app.services.llm import client

    return {
        "openai_api_key_configured": bool(settings.OPENAI_API_KEY),
        "openai_api_key_length": len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0,
        "client_initialized": client is not None,
        "llm_provider": settings.LLM_PROVIDER,
    }


@router.get("/debug/test")
def debug_test():
    return {"status": "ok", "message": "Le serveur répond correctement"}
