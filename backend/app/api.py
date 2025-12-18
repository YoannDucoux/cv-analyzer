import logging
import os
import uuid
import inspect
from typing import Optional, List, Tuple

from fastapi import APIRouter, UploadFile, File, HTTPException, Form

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
        logger.error(f"Erreur extraction pour {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur extraction: {str(e)}"
        )

    try:
        # analyze_cv peut être sync OU async selon ta version -> on gère les deux
        result = await _maybe_await(
            analyze_cv(
                cv_text=cv_text,
                extraction_warnings=warnings,
                job_description=job_description,
            )
        )
        return result
    except Exception as e:
        logger.error(f"Erreur analyse CV: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )


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

