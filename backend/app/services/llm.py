from __future__ import annotations

import json
from openai import OpenAI

from app.core.config import settings
from app.models.cv import (
    CVCanonical,
    ATSAssessment,
    CVInsights,
    ATSSubScores,
    JobMatching,
    KeywordMatching,
    KeywordMatch,
    KeywordMatchStatus,
    KeywordCategory,
    CVComparisonResult,
    CVComparisonItem,
    ComparisonCriterion,
)

# Client OpenAI initialisé uniquement si la clé est disponible
client: OpenAI | None = None
if getattr(settings, "OPENAI_API_KEY", None):
    client = OpenAI(api_key=settings.OPENAI_API_KEY)


def llm_canonicalize(cv_text: str, extraction_warnings: list[str]) -> CVCanonical:
    """
    Extrait et structure le CV en format canonique via OpenAI.
    """
    if not client:
        return CVCanonical(
            summary=None,
            extraction_warnings=extraction_warnings + ["OpenAI API key non configurée (OPENAI_API_KEY manquant)."],
        )

    prompt = f"""Tu es un expert en extraction de données de CV. Analyse le texte suivant et extrais les informations structurées.

Texte du CV:
{cv_text[:8000]}

Extrais les informations suivantes au format JSON strict (pas de markdown, juste du JSON):
- full_name: nom complet
- headline: titre/profession
- email: adresse email
- phone: numéro de téléphone
- location: localisation
- summary: résumé professionnel
- experiences: liste d'objets avec title, company, location, dates (start, end, is_current), bullets, skills
- education: liste d'objets avec degree, school, location, dates, details
- hard_skills: liste de compétences techniques
- soft_skills: liste de compétences comportementales
- tools: liste d'outils/logiciels
- languages: liste d'objets avec name et level
- certifications: liste de certifications
- links: liste d'objets avec label et url

Réponds UNIQUEMENT avec un JSON valide, sans texte avant ou après."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un expert en extraction de données structurées. Tu réponds toujours en JSON valide."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Réponse vide de l'API OpenAI")

        result = json.loads(response.choices[0].message.content)

        # Valider et créer le modèle avec gestion des erreurs de validation
        try:
            canonical = CVCanonical(**result)
        except Exception as validation_error:
            # Si la validation échoue, créer un modèle minimal avec les données disponibles
            canonical = CVCanonical()
            if "full_name" in result:
                canonical.full_name = result.get("full_name")
            if "email" in result:
                canonical.email = result.get("email")
            if "experiences" in result:
                canonical.experiences = result.get("experiences", [])
            if "hard_skills" in result:
                canonical.hard_skills = result.get("hard_skills", [])
            canonical.extraction_warnings = extraction_warnings + [f"Validation partielle: {str(validation_error)}"]
            return canonical

        canonical.extraction_warnings = extraction_warnings
        return canonical

    except json.JSONDecodeError as e:
        return CVCanonical(
            summary=None,
            extraction_warnings=extraction_warnings + [f"Erreur parsing JSON: {str(e)}"],
        )
    except Exception as e:
        error_msg = str(e)
        # Gestion spécifique des erreurs OpenAI
        if "429" in error_msg or "insufficient_quota" in error_msg.lower():
            user_message = "Quota OpenAI dépassé. Vérifiez votre plan et vos factures sur https://platform.openai.com/account/billing"
        elif "401" in error_msg or "invalid_api_key" in error_msg.lower():
            user_message = "Clé API OpenAI invalide. Vérifiez la variable d'environnement OPENAI_API_KEY."
        elif "rate_limit" in error_msg.lower():
            user_message = "Limite de taux OpenAI atteinte. Veuillez réessayer dans quelques instants."
        else:
            user_message = f"Erreur LLM: {error_msg[:200]}"

        return CVCanonical(
            summary=None,
            extraction_warnings=extraction_warnings + [user_message],
        )


def llm_ats_and_insights(canonical: CVCanonical) -> tuple[ATSAssessment, CVInsights]:
    """
    Analyse le CV pour générer un score ATS et des insights via OpenAI.
    """
    if not client:
        ats = ATSAssessment(
            total_score=50,
            subscores=ATSSubScores(
                readability=50,
                structure=50,
                chronology=50,
                evidence=50,
                skills_clarity=50,
            ),
            issues=["OpenAI API key non configurée (OPENAI_API_KEY manquant)."],
            quick_wins=["Configurer OPENAI_API_KEY pour obtenir un diagnostic ATS."],
        )
        insights = CVInsights(
            positioning=[],
            strengths=[],
            blind_spots=[],
            rewrite_suggestions=[],
        )
        return ats, insights

    canonical_json = canonical.model_dump_json()

    prompt = f"""Tu es un expert en ATS (Applicant Tracking System) et en optimisation de CV. Analyse le CV suivant et génère un score ATS détaillé ainsi que des insights.

CV structuré:
{canonical_json[:6000]}

Génère un JSON avec:
- ats: objet avec total_score (0-100), subscores (readability, structure, chronology, evidence, skills_clarity tous 0-100), issues (liste de problèmes), quick_wins (liste de suggestions rapides)
- insights: objet avec positioning (suggestions de positionnement), strengths (points forts), blind_spots (angles morts), rewrite_suggestions (suggestions de réécriture)

Réponds UNIQUEMENT avec un JSON valide avec les clés "ats" et "insights"."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un expert en ATS et optimisation de CV. Tu réponds toujours en JSON valide."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Réponse vide de l'API OpenAI")

        result = json.loads(response.choices[0].message.content)

        # Extraire et valider les données ATS
        ats_data = result.get("ats", {})
        subscores_data = ats_data.get("subscores", {})

        def clamp_score(score, default=50):
            try:
                score_i = int(score)
                return max(0, min(100, score_i))
            except (ValueError, TypeError):
                return default

        ats = ATSAssessment(
            total_score=clamp_score(ats_data.get("total_score", 50)),
            subscores=ATSSubScores(
                readability=clamp_score(subscores_data.get("readability", 50)),
                structure=clamp_score(subscores_data.get("structure", 50)),
                chronology=clamp_score(subscores_data.get("chronology", 50)),
                evidence=clamp_score(subscores_data.get("evidence", 50)),
                skills_clarity=clamp_score(subscores_data.get("skills_clarity", 50)),
            ),
            issues=ats_data.get("issues", []) if isinstance(ats_data.get("issues"), list) else [],
            quick_wins=ats_data.get("quick_wins", []) if isinstance(ats_data.get("quick_wins"), list) else [],
        )

        # Extraire et valider les insights
        insights_data = result.get("insights", {})
        insights = CVInsights(
            positioning=insights_data.get("positioning", []) if isinstance(insights_data.get("positioning"), list) else [],
            strengths=insights_data.get("strengths", []) if isinstance(insights_data.get("strengths"), list) else [],
            blind_spots=insights_data.get("blind_spots", []) if isinstance(insights_data.get("blind_spots"), list) else [],
            rewrite_suggestions=insights_data.get("rewrite_suggestions", []) if isinstance(insights_data.get("rewrite_suggestions"), list) else [],
        )

        return ats, insights

    except json.JSONDecodeError as e:
        ats = ATSAssessment(
            total_score=50,
            subscores=ATSSubScores(
                readability=50,
                structure=50,
                chronology=50,
                evidence=50,
                skills_clarity=50,
            ),
            issues=[f"Erreur parsing JSON: {str(e)}"],
            quick_wins=[],
        )
        insights = CVInsights(
            positioning=[],
            strengths=[],
            blind_spots=[],
            rewrite_suggestions=[],
        )
        return ats, insights
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "insufficient_quota" in error_msg.lower():
            user_message = "Quota OpenAI dépassé. Rechargez votre compte sur https://platform.openai.com/account/billing"
        elif "401" in error_msg or "invalid_api_key" in error_msg.lower():
            user_message = "Clé API OpenAI invalide (OPENAI_API_KEY)."
        elif "rate_limit" in error_msg.lower():
            user_message = "Limite de taux atteinte, réessayez plus tard."
        else:
            user_message = f"Erreur LLM: {error_msg[:200]}"

        ats = ATSAssessment(
            total_score=50,
            subscores=ATSSubScores(
                readability=50,
                structure=50,
                chronology=50,
                evidence=50,
                skills_clarity=50,
            ),
            issues=[user_message],
            quick_wins=["Vérifiez votre crédit OpenAI pour obtenir une analyse complète."],
        )
        insights = CVInsights(
            positioning=[],
            strengths=[],
            blind_spots=[],
            rewrite_suggestions=[],
        )
        return ats, insights


def llm_job_matching(canonical: CVCanonical, job_description: str) -> JobMatching:
    """
    Compare le CV avec une offre d'emploi et génère un score d'adéquation via OpenAI.
    """
    if not client:
        return JobMatching(
            overall_score=0,
            skills_match=0,
            experience_match=0,
            education_match=0,
            missing_requirements=["OpenAI API key non configurée (OPENAI_API_KEY manquant)."],
            strengths=[],
            recommendations=[],
        )

    canonical_json = canonical.model_dump_json()

    prompt = f"""Tu es un expert en recrutement. Compare le CV suivant avec l'offre d'emploi et évalue le degré d'adéquation.

CV structuré:
{canonical_json[:6000]}

Offre d'emploi:
{job_description[:4000]}

Génère un JSON avec:
- overall_score: score global d'adéquation (0-100)
- skills_match: adéquation des compétences (0-100)
- experience_match: adéquation de l'expérience (0-100)
- education_match: adéquation de la formation (0-100)
- missing_requirements: liste des exigences manquantes
- strengths: liste des points forts par rapport à l'offre
- recommendations: liste de recommandations pour améliorer l'adéquation

Réponds UNIQUEMENT avec un JSON valide."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un expert en recrutement et matching CV/offre. Tu réponds toujours en JSON valide."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Réponse vide de l'API OpenAI")

        result = json.loads(response.choices[0].message.content)

        def clamp_score(score, default=0):
            try:
                score_i = int(score)
                return max(0, min(100, score_i))
            except (ValueError, TypeError):
                return default

        return JobMatching(
            overall_score=clamp_score(result.get("overall_score", 0)),
            skills_match=clamp_score(result.get("skills_match", 0)),
            experience_match=clamp_score(result.get("experience_match", 0)),
            education_match=clamp_score(result.get("education_match", 0)),
            missing_requirements=result.get("missing_requirements", []) if isinstance(result.get("missing_requirements"), list) else [],
            strengths=result.get("strengths", []) if isinstance(result.get("strengths"), list) else [],
            recommendations=result.get("recommendations", []) if isinstance(result.get("recommendations"), list) else [],
        )

    except json.JSONDecodeError as e:
        return JobMatching(
            overall_score=0,
            skills_match=0,
            experience_match=0,
            education_match=0,
            missing_requirements=[f"Erreur parsing JSON: {str(e)}"],
            strengths=[],
            recommendations=[],
        )
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "insufficient_quota" in error_msg.lower():
            user_message = "Quota OpenAI dépassé. Rechargez votre compte pour analyser l'adéquation CV/offre."
        elif "401" in error_msg or "invalid_api_key" in error_msg.lower():
            user_message = "Clé API OpenAI invalide (OPENAI_API_KEY)."
        elif "rate_limit" in error_msg.lower():
            user_message = "Limite de taux atteinte, réessayez plus tard."
        else:
            user_message = f"Erreur LLM: {error_msg[:200]}"

        return JobMatching(
            overall_score=0,
            skills_match=0,
            experience_match=0,
            education_match=0,
            missing_requirements=[user_message],
            strengths=[],
            recommendations=["Vérifiez votre crédit OpenAI sur https://platform.openai.com/account/billing"],
        )


def llm_keyword_matching(canonical: CVCanonical, job_description: str) -> KeywordMatching:
    """
    Extrait les mots-clés de l'offre et compare avec le CV pour déterminer leur présence.
    """
    if not client:
        return KeywordMatching(
            keywords=[],
            coverage_score=0,
            critical_missing=["OpenAI API key non configurée (OPENAI_API_KEY manquant)."],
        )

    canonical_json = canonical.model_dump_json()

    prompt = f"""Tu es un expert en recrutement et analyse de CV. Analyse l'offre d'emploi suivante et compare-la avec le CV pour identifier la correspondance des mots-clés.

CV structuré:
{canonical_json[:6000]}

Offre d'emploi:
{job_description[:4000]}

Tâches:
1. Extrais les mots-clés importants de l'offre (compétences techniques, compétences comportementales, outils, formations, expériences requises)
2. Pour chaque mot-clé, détermine s'il est présent, partiellement présent ou absent dans le CV
3. Si présent ou partiel, indique l'élément du CV qui sert de preuve
4. Évalue l'importance de chaque mot-clé (1=faible, 5=critique pour le poste)
5. Calcule un score de couverture global (0-100)

Génère un JSON avec:
- keywords: liste d'objets avec:
  - keyword: le mot-clé ou compétence
  - category: "technical_skill", "soft_skill", "tool", "education", "experience", ou "other"
  - status: "present", "partial", ou "absent"
  - evidence: élément du CV qui prouve la présence (si présent ou partiel), null si absent
  - importance: 1 à 5 (5 = critique)
- coverage_score: score de couverture global (0-100)
- critical_missing: liste des mots-clés critiques (importance >= 4) absents du CV

Réponds UNIQUEMENT avec un JSON valide."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un expert en extraction de mots-clés et matching CV/offre. Tu réponds toujours en JSON valide."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Réponse vide de l'API OpenAI")

        result = json.loads(response.choices[0].message.content)

        keywords_data = result.get("keywords", [])
        keyword_matches: list[KeywordMatch] = []

        for kw_data in keywords_data:
            try:
                status_str = str(kw_data.get("status", "absent")).lower()
                if status_str == "present":
                    status = KeywordMatchStatus.PRESENT
                elif status_str == "partial":
                    status = KeywordMatchStatus.PARTIAL
                else:
                    status = KeywordMatchStatus.ABSENT

                category_str = str(kw_data.get("category", "other")).lower()
                category_map = {
                    "technical_skill": KeywordCategory.TECHNICAL_SKILL,
                    "soft_skill": KeywordCategory.SOFT_SKILL,
                    "tool": KeywordCategory.TOOL,
                    "education": KeywordCategory.EDUCATION,
                    "experience": KeywordCategory.EXPERIENCE,
                }
                category = category_map.get(category_str, KeywordCategory.OTHER)

                importance_raw = kw_data.get("importance", 3)
                try:
                    importance = int(importance_raw)
                except (ValueError, TypeError):
                    importance = 3
                importance = min(5, max(1, importance))

                keyword_matches.append(
                    KeywordMatch(
                        keyword=str(kw_data.get("keyword", "")),
                        category=category,
                        status=status,
                        evidence=kw_data.get("evidence"),
                        importance=importance,
                    )
                )
            except Exception:
                continue  # ignorer les mots-clés mal formés

        coverage_raw = result.get("coverage_score", 0)
        try:
            coverage_score = int(coverage_raw)
        except (ValueError, TypeError):
            coverage_score = 0
        coverage_score = min(100, max(0, coverage_score))

        critical_missing = result.get("critical_missing", [])
        if not isinstance(critical_missing, list):
            critical_missing = []

        return KeywordMatching(
            keywords=keyword_matches,
            coverage_score=coverage_score,
            critical_missing=critical_missing,
        )

    except json.JSONDecodeError as e:
        return KeywordMatching(
            keywords=[],
            coverage_score=0,
            critical_missing=[f"Erreur parsing JSON: {str(e)}"],
        )
    except Exception as e:
        error_msg = str(e)
        return KeywordMatching(
            keywords=[],
            coverage_score=0,
            critical_missing=[f"Erreur LLM: {error_msg[:200]}"],
        )


def llm_compare_cvs(cvs_data: list[tuple[str, str, CVCanonical]], job_description: str) -> CVComparisonResult:
    """
    Compare plusieurs CV pour une même offre d'emploi et génère un classement.

    Args:
        cvs_data: Liste de tuples (cv_id, filename, canonical)
        job_description: Texte de l'offre d'emploi
    """
    if not client:
        return CVComparisonResult(
            job_description=job_description,
            cvs=[],
            overall_ranking=[],
            criteria_comparison=[],
            summary="OpenAI API key non configurée (OPENAI_API_KEY manquant).",
        )

    if len(cvs_data) < 2:
        return CVComparisonResult(
            job_description=job_description,
            cvs=[],
            overall_ranking=[],
            criteria_comparison=[],
            summary="Au moins 2 CV sont nécessaires pour une comparaison.",
        )

    cvs_info = []
    for cv_id, filename, canonical in cvs_data:
        cvs_info.append(
            {
                "id": cv_id,
                "filename": filename,
                "data": canonical.model_dump_json()[:4000],
            }
        )

    cvs_description = []
    for i, cv_info in enumerate(cvs_info):
        cvs_description.append(f"{i+1}. CV ID: '{cv_info['id']}' - Fichier: {cv_info['filename']}")

    cv_ids_list = [cv_info["id"] for cv_info in cvs_info]

    prompt = f"""Tu es un expert en recrutement et comparaison de CV. Compare les {len(cvs_data)} CV suivants pour l'offre d'emploi donnée.

Offre d'emploi:
{job_description[:4000]}

CVs à comparer (utilise EXACTEMENT ces IDs dans ta réponse):
{chr(10).join(cvs_description)}

IDs valides à utiliser: {', '.join([f"'{id}'" for id in cv_ids_list])}

Données des CVs:
{json.dumps(cvs_info, ensure_ascii=False)[:12000]}

Tâches:
1. Pour chaque CV, calcule:
   - matching_score: score global de correspondance avec l'offre (0-100)
   - skills_score: score de correspondance des compétences (0-100)
   - experience_score: score de correspondance de l'expérience (0-100)
   - education_score: score de correspondance de la formation (0-100)
   - keyword_coverage: taux de couverture des mots-clés de l'offre (0-100)
   - justification: justification textuelle courte (2-3 phrases) de la correspondance

2. Classe les CV du meilleur au moins bon (overall_ranking: liste des IDs)

3. Pour chaque critère (compétences, expérience, formation), identifie:
   - Le CV le mieux noté
   - Le classement complet
   - Une justification du classement

4. Génère un résumé global de la comparaison (3-4 phrases)

Génère un JSON avec:
- cvs: liste d'objets (un pour chaque CV), chacun avec:
  - cv_id: l'ID EXACT du CV tel que fourni dans "CV ID: ..." ci-dessus
  - matching_score: score global de correspondance (0-100)
  - skills_score: score de correspondance des compétences (0-100)
  - experience_score: score de correspondance de l'expérience (0-100)
  - education_score: score de correspondance de la formation (0-100)
  - keyword_coverage: taux de couverture des mots-clés de l'offre (0-100)
  - justification: justification textuelle courte (2-3 phrases)
- overall_ranking: liste des cv_id dans l'ordre du meilleur au moins bon
- criteria_comparison: liste d'objets avec:
  - criterion_name: nom du critère (ex: "Compétences techniques", "Expérience", "Formation")
  - best_cv_id: cv_id du meilleur CV pour ce critère
  - ranking: liste des cv_id classés du meilleur au moins bon
  - justification: justification du classement
- summary: résumé textuel de la comparaison (3-4 phrases)

CRITIQUE: Utilise EXACTEMENT les IDs fournis. Réponds UNIQUEMENT avec un JSON valide."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Tu es un expert en comparaison de CV et recrutement. Tu réponds toujours en JSON valide."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Réponse vide de l'API OpenAI")

        result = json.loads(response.choices[0].message.content)

        cvs_items: list[CVComparisonItem] = []
        def clamp_score(score, default=0):
            try:
                return max(0, min(100, int(score)))
            except (ValueError, TypeError):
                return default

        cvs_result = result.get("cvs", [])
        if not isinstance(cvs_result, list):
            cvs_result = []

        # Construire les items en essayant de matcher par cv_id ou filename
        for (cv_id, filename, canonical) in cvs_data:
            cv_result_data = None
            for cv_res in cvs_result:
                if not isinstance(cv_res, dict):
                    continue
                if (cv_res.get("cv_id") == cv_id) or (cv_res.get("filename") == filename) or (cv_res.get("id") == cv_id):
                    cv_result_data = cv_res
                    break

            if cv_result_data is None and cvs_result:
                # fallback par position si possible
                idx = [x[0] for x in cvs_data].index(cv_id)
                if idx < len(cvs_result) and isinstance(cvs_result[idx], dict):
                    cv_result_data = cvs_result[idx]

            if cv_result_data:
                cvs_items.append(
                    CVComparisonItem(
                        cv_id=cv_id,
                        filename=filename,
                        canonical=canonical,
                        matching_score=clamp_score(cv_result_data.get("matching_score", 0)),
                        skills_score=clamp_score(cv_result_data.get("skills_score", 0)),
                        experience_score=clamp_score(cv_result_data.get("experience_score", 0)),
                        education_score=clamp_score(cv_result_data.get("education_score", 0)),
                        keyword_coverage=clamp_score(cv_result_data.get("keyword_coverage", 0)),
                        justification=str(cv_result_data.get("justification", "")),
                        keyword_matching=None,
                    )
                )
            else:
                cvs_items.append(
                    CVComparisonItem(
                        cv_id=cv_id,
                        filename=filename,
                        canonical=canonical,
                        matching_score=0,
                        skills_score=0,
                        experience_score=0,
                        education_score=0,
                        keyword_coverage=0,
                        justification="Analyse en cours...",
                        keyword_matching=None,
                    )
                )

        criteria: list[ComparisonCriterion] = []
        crit_list = result.get("criteria_comparison", [])
        if isinstance(crit_list, list):
            for crit_data in crit_list:
                if not isinstance(crit_data, dict):
                    continue
                criteria.append(
                    ComparisonCriterion(
                        criterion_name=str(crit_data.get("criterion_name", "")),
                        best_cv_id=str(crit_data.get("best_cv_id", "")),
                        ranking=crit_data.get("ranking", []) if isinstance(crit_data.get("ranking"), list) else [],
                        justification=str(crit_data.get("justification", "")),
                    )
                )

        overall_ranking = result.get("overall_ranking", [])
        if not overall_ranking or not isinstance(overall_ranking, list):
            overall_ranking = [cv.cv_id for cv in sorted(cvs_items, key=lambda x: x.matching_score, reverse=True)]

        return CVComparisonResult(
            job_description=job_description,
            cvs=cvs_items,
            overall_ranking=overall_ranking,
            criteria_comparison=criteria,
            summary=str(result.get("summary", "")),
        )

    except json.JSONDecodeError as e:
        return CVComparisonResult(
            job_description=job_description,
            cvs=[],
            overall_ranking=[],
            criteria_comparison=[],
            summary=f"Erreur parsing JSON: {str(e)}",
        )
    except Exception as e:
        error_msg = str(e)
        return CVComparisonResult(
            job_description=job_description,
            cvs=[],
            overall_ranking=[],
            criteria_comparison=[],
            summary=f"Erreur LLM: {error_msg[:200]}",
        )

