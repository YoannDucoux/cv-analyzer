from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DateRange(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None
    is_current: Optional[bool] = None


class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    dates: Optional[DateRange] = None
    bullets: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    degree: Optional[str] = None
    school: Optional[str] = None
    location: Optional[str] = None
    dates: Optional[DateRange] = None
    details: List[str] = Field(default_factory=list)


class LanguageItem(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None


class LinkItem(BaseModel):
    label: Optional[str] = None
    url: Optional[str] = None


class CVCanonical(BaseModel):
    full_name: Optional[str] = None
    headline: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None

    experiences: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)

    hard_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)

    languages: List[LanguageItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    links: List[LinkItem] = Field(default_factory=list)

    extraction_warnings: List[str] = Field(default_factory=list)


class ATSSubScores(BaseModel):
    readability: int = 50
    structure: int = 50
    chronology: int = 50
    evidence: int = 50
    skills_clarity: int = 50


class ATSAssessment(BaseModel):
    total_score: int = 50
    subscores: ATSSubScores = Field(default_factory=ATSSubScores)
    issues: List[str] = Field(default_factory=list)
    quick_wins: List[str] = Field(default_factory=list)


class CVInsights(BaseModel):
    positioning: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    blind_spots: List[str] = Field(default_factory=list)
    rewrite_suggestions: List[str] = Field(default_factory=list)


class KeywordMatchStatus(str, Enum):
    PRESENT = "present"
    PARTIAL = "partial"
    ABSENT = "absent"


class KeywordCategory(str, Enum):
    TECHNICAL_SKILL = "technical_skill"
    SOFT_SKILL = "soft_skill"
    TOOL = "tool"
    EDUCATION = "education"
    EXPERIENCE = "experience"
    OTHER = "other"


class KeywordMatch(BaseModel):
    keyword: str = ""
    category: KeywordCategory = KeywordCategory.OTHER
    status: KeywordMatchStatus = KeywordMatchStatus.ABSENT
    evidence: Optional[str] = None
    importance: int = 3


class KeywordMatching(BaseModel):
    keywords: List[KeywordMatch] = Field(default_factory=list)
    coverage_score: int = 0
    critical_missing: List[str] = Field(default_factory=list)


class JobMatching(BaseModel):
    overall_score: int = 0
    skills_match: int = 0
    experience_match: int = 0
    education_match: int = 0
    missing_requirements: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    keyword_matching: Optional[KeywordMatching] = None


class ComparisonCriterion(BaseModel):
    criterion_name: str = ""
    best_cv_id: str = ""
    ranking: List[str] = Field(default_factory=list)
    justification: str = ""


class CVComparisonItem(BaseModel):
    cv_id: str
    filename: str
    canonical: CVCanonical

    matching_score: int = 0
    skills_score: int = 0
    experience_score: int = 0
    education_score: int = 0
    keyword_coverage: int = 0
    justification: str = ""

    keyword_matching: Optional[KeywordMatching] = None


class CVComparisonResult(BaseModel):
    job_description: str = ""
    cvs: List[CVComparisonItem] = Field(default_factory=list)
    overall_ranking: List[str] = Field(default_factory=list)
    criteria_comparison: List[ComparisonCriterion] = Field(default_factory=list)
    summary: str = ""


class CVAnalysisResponse(BaseModel):
    canonical: CVCanonical
    ats: ATSAssessment
    insights: CVInsights
    job_matching: Optional[JobMatching] = None


# IMPORTANT: alias attendu par tes imports
CvAnalysisResponse = CVAnalysisResponse
