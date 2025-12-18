import logging
import os
import uuid
import inspect
from typing import Optional, List, Tuple

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import PlainTextResponse

from app.services.extract_text import extract_text_from_file
from app.services.analyze import analyze_cv
from app.services.llm import (
    llm_compare_cvs,
    llm_canonicalize,
    llm_keyword_matching,
)
from app.services.scoring import fallback_scoring_if_needed
from app.models.cv import CvAnalysisResponse, CVComparisonResult

router = APIRouter()
logger = logging.getLogger(__name__)

# =========================
# Sécurité / limites
# =========================
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

# Activer debug uniquement si ENABLE_DEBUG=true côté environnement (Render)
ENABLE_DEBUG = os.getenv("ENABLE_DEBUG", "false").strip().lower() == "true"


async def _maybe_await(value):
    """Permet d'appeler des fonctions sync ou async sans se tromper."""
    if inspect.isawaitable(value):
        return await value
    return value


async def _read_and_validate_file(file: UploadFile) -> bytes:
    # 1) Valider le type MIME
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Format non supporté. PDF ou DOCX uniquement.",
        )

    # 2) Lire le fichier
    raw_bytes = await file.read()

    # 3) Valider la taille réelle
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Fichier trop volumineux (taille maximale : {MAX_FILE_SIZE_MB} Mo).",
        )

    # 4) Valider non-vide
    if not raw_bytes:
        raise HTTPException(status_code=400, detail="Fichier vide.")

    return raw_bytes


@router.post("/analyze-cv", response_model=CvAnalysisResponse)
async def analyze_cv_endpoint(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
):
    raw_bytes = await _read_and_validate_file(file)

    try:
        cv_text, warnings = extract_text_from_file(raw_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur extraction: {e}")

    # analyze_cv peut être sync OU async selon ta version -> on gère les deux
    result = await _maybe_await(
        analyze_cv(
            cv_text=cv_text,
            extraction_warnings=warnings,
            job_description=job_description,
        )
    )
    return result


@router.post("/compare-cvs", response_model=CVComparisonResult)
async def compare_cvs_endpoint(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...),
):
    if len(files) < 2:
        raise HTTPException(
            status_code=400,
            detail="Au moins 2 CV sont nécessaires pour une comparaison.",
        )

    cvs_data: List[Tuple[str, str, object]] = []

    for f in files:
        raw_bytes = await _read_and_validate_file(f)

        try:
            cv_text, warnings = extract_text_from_file(raw_bytes, f.filename)

            canonical = await _maybe_await(llm_canonicalize(cv_text, warnings))
            canonical = fallback_scoring_if_needed(canonical)

            cv_id = str(uuid.uuid4())[:8]
            cvs_data.append((cv_id, f.filename, canonical))

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur extraction pour {f.filename}: {e}",
            )

    try:
        # Comparaison (sync ou async)
        result: CVComparisonResult = await _maybe_await(llm_compare_cvs(cvs_data, job_description))

        # Enrichir chaque CV avec matching mots-clés (sync ou async)
        for cv_item in result.cvs:
            try:
                keyword_matching = await _maybe_await(
                    llm_keyword_matching(cv_item.canonical, job_description)
                )
                cv_item.keyword_matching = keyword_matching
            except Exception as e:
                logger.warning(f"Erreur analyse mots-clés pour {cv_item.filename}: {e}")

        return result

    except Exception as e:
        logger.error("Erreur lors de la comparaison", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la comparaison: {str(e)}",
        )


# =========================
# Debug endpoints (désactivés par défaut en prod)
# =========================
if ENABLE_DEBUG:

    @router.post("/debug/extract-text", response_class=PlainTextResponse)
    async def debug_extract_text(file: UploadFile = File(...)):
        raw_bytes = await _read_and_validate_file(file)
        cv_text, _warnings = extract_text_from_file(raw_bytes, file.filename)
        return cv_text

    @router.get("/debug/config")
    def debug_config():
        from app.core.config import settings
        from app.services.llm import client

        return {
            "openai_api_key_configured": bool(settings.OPENAI_API_KEY),
            "openai_api_key_length": len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0,
            "client_initialized": client is not None,
            "llm_provider": settings.LLM_PROVIDER,
            "enable_debug": True,
        }

    @router.get("/debug/test")
    def debug_test():
        return {"status": "ok", "message": "Le serveur répond correctement", "enable_debug": True}

