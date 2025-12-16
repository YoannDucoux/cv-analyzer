from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import PlainTextResponse
from typing import Optional, List
from .services.extract_text import extract_text_from_file
from .services.analyze import analyze_cv
from .services.llm import llm_compare_cvs
from .models.cv import CvAnalysisResponse, CVComparisonResult, CVCanonical
import uuid

router = APIRouter()


@router.post("/analyze-cv", response_model=CvAnalysisResponse)
async def analyze_cv_endpoint(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None)
):
    allowed = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Format non supporté. PDF ou DOCX uniquement.")

    raw_bytes = await file.read()

    try:
        cv_text, warnings = extract_text_from_file(raw_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur extraction: {e}")

    result = await analyze_cv(
        cv_text=cv_text, 
        extraction_warnings=warnings,
        job_description=job_description
    )
    return result


@router.post("/debug/extract-text", response_class=PlainTextResponse)
async def debug_extract_text(file: UploadFile = File(...)):
    raw_bytes = await file.read()
    cv_text, _warnings = extract_text_from_file(raw_bytes, file.filename)
    return cv_text


@router.post("/compare-cvs", response_model=CVComparisonResult)
async def compare_cvs_endpoint(
    files: List[UploadFile] = File(...),
    job_description: str = Form(...)
):
    """
    Compare plusieurs CV pour une même offre d'emploi.
    Nécessite au moins 2 fichiers CV et une description d'offre.
    
    Note: FastAPI attend que tous les fichiers aient le même nom de champ "files"
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Reçu {len(files)} fichiers pour comparaison")
    
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Au moins 2 CV sont nécessaires pour une comparaison.")
    
    allowed = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }
    
    # Extraire et analyser chaque CV
    cvs_data = []
    from .services.llm import llm_canonicalize, llm_keyword_matching
    from .services.scoring import fallback_scoring_if_needed
    
    for file in files:
        if file.content_type not in allowed:
            raise HTTPException(status_code=400, detail=f"Format non supporté pour {file.filename}. PDF ou DOCX uniquement.")
        
        raw_bytes = await file.read()
        
        try:
            cv_text, warnings = extract_text_from_file(raw_bytes, file.filename)
            canonical = await llm_canonicalize(cv_text, warnings)
            canonical = fallback_scoring_if_needed(canonical)
            
            cv_id = str(uuid.uuid4())[:8]
            cvs_data.append((cv_id, file.filename, canonical))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur extraction pour {file.filename}: {e}")
    
    try:
        # Comparer les CV
        result = await llm_compare_cvs(cvs_data, job_description)
        
        # Enrichir chaque CV avec l'analyse des mots-clés
        from .services.llm import llm_keyword_matching
        for cv_item in result.cvs:
            try:
                keyword_matching = await llm_keyword_matching(cv_item.canonical, job_description)
                cv_item.keyword_matching = keyword_matching
            except Exception as e:
                logger.warning(f"Erreur lors de l'analyse des mots-clés pour {cv_item.filename}: {e}")
                # Continuer même si l'analyse des mots-clés échoue
        
        return result
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la comparaison: {str(e)}")


@router.get("/debug/config")
async def debug_config():
    """Endpoint de diagnostic pour vérifier la configuration OpenAI"""
    from .core.config import settings
    from .services.llm import client
    
    return {
        "openai_api_key_configured": bool(settings.OPENAI_API_KEY),
        "openai_api_key_length": len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0,
        "openai_api_key_prefix": settings.OPENAI_API_KEY[:7] + "..." if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 7 else None,
        "client_initialized": client is not None,
        "llm_provider": settings.LLM_PROVIDER,
    }

@router.get("/debug/test")
async def debug_test():
    """Endpoint de test simple pour vérifier que le serveur répond"""
    return {"status": "ok", "message": "Le serveur répond correctement"}
