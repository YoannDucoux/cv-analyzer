from ..models.cv import CVCanonical

def fallback_scoring_if_needed(canonical: CVCanonical) -> CVCanonical:
    """
    Si l'extraction/LLM renvoie quelque chose de trop vide,
    on garde au moins les warnings. (Tu enrichiras plus tard.)
    """
    if (
        canonical.full_name is None
        and canonical.headline is None
        and canonical.summary is None
        and not canonical.experiences
        and not canonical.education
        and not canonical.hard_skills
        and not canonical.tools
    ):
        canonical.extraction_warnings.append(
            "Le CV structuré est très vide. Vérifie l'extraction ou fournis un CV en DOCX."
        )
    return canonical
