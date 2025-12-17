from __future__ import annotations

from app.models.cv import CvAnalysisResponse, CVCanonical, JobMatching
from app.services.llm import (
    llm_canonicalize,
    llm_ats_and_insights,
    llm_job_matching,
    llm_keyword_matching,
)
from app.services.scoring import fallback_scoring_if_needed


def analyze_cv(
    cv_text: str,
    extraction_warnings: list[str],
    job_description: str | None = None,
) -> CvAnalysisResponse:
    canonical: CVCanonical = llm_canonicalize(cv_text, extraction_warnings)
    canonical = fallback_scoring_if_needed(canonical)

    ats, insights = llm_ats_and_insights(canonical)

    job_matching: JobMatching | None = None
    if job_description:
        job_matching = llm_job_matching(canonical, job_description)
        keyword_matching = llm_keyword_matching(canonical, job_description)
        if job_matching is not None:
            job_matching.keyword_matching = keyword_matching

    return CvAnalysisResponse(
        canonical=canonical,
        ats=ats,
        insights=insights,
        job_matching=job_matching,
    )
