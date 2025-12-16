from ..models.cv import CvAnalysisResponse, CVCanonical, JobMatching
from .llm import llm_canonicalize, llm_ats_and_insights, llm_job_matching, llm_keyword_matching
from .scoring import fallback_scoring_if_needed

async def analyze_cv(cv_text: str, extraction_warnings: list[str], job_description: str | None = None) -> CvAnalysisResponse:
    canonical: CVCanonical = await llm_canonicalize(cv_text, extraction_warnings)
    canonical = fallback_scoring_if_needed(canonical)

    ats, insights = await llm_ats_and_insights(canonical)
    
    job_matching = None
    if job_description:
        # Analyser le matching global
        job_matching = await llm_job_matching(canonical, job_description)
        
        # Analyser les mots-clés
        keyword_matching = await llm_keyword_matching(canonical, job_description)
        
        # Intégrer les mots-clés dans le job_matching
        if job_matching:
            job_matching.keyword_matching = keyword_matching

    return CvAnalysisResponse(
        canonical=canonical,
        ats=ats,
        insights=insights,
        job_matching=job_matching,
    )
