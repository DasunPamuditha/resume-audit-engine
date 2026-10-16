# backend/xai_explainer.py

from typing import List, Dict, Any


class XAIExplainer:
    def __init__(self, extracted_skills: List[str], audit_results: Dict):
        self.extracted_skills = [s.lower() for s in extracted_skills]
        self.audit_results = audit_results

    def generate_explanation(self) -> Dict:
        lang_distribution = self.audit_results.get("language_distribution", {})
        anomalies = self.audit_results.get("anomalies", [])
        dep_verified = self.audit_results.get("dependency_verified", False)

        skill_breakdown = {}
        recommendations = []
        core_languages = ["python", "javascript", "java"]

        for lang in core_languages:
            score = lang_distribution.get(lang, 0.0)
            if score > 0.15:
                status = "Confirmed in GitHub Code"
            elif score > 0.0:
                status = "Found (Small Amount of Code)"
                recommendations.append(
                    f"Add more {lang.capitalize()} code commits to make your public projects stronger."
                )
            else:
                status = "Not Found in Public Code"
                if lang in self.extracted_skills:
                    recommendations.append(
                        f"'{lang.capitalize()}' is written on the resume, but no {lang.capitalize()} code was found on GitHub."
                    )

            skill_breakdown[lang] = {
                "status": status,
                "confidence_weight": round(score * 100, 2)
            }

        if not dep_verified:
            recommendations.append(
                "Include project setup files (such as requirements.txt, package.json, or pom.xml) to prove which libraries were used."
            )

        if anomalies:
            recommendations.append(
                "Push code step-by-step as you build it rather than uploading finished folders all at once."
            )

        return {
            "skill_verification_breakdown": skill_breakdown,
            "upskilling_recommendations": recommendations,
            "forensic_warning_flags": anomalies
        }


def generate_xai_rationale(*args, **kwargs) -> str:
    candidate = kwargs.get("candidate_name", "The candidate")
    score = kwargs.get("confidence_score", kwargs.get("score", "N/A"))

    skill_gap = kwargs.get("skill_gap_data") or kwargs.get("skill_gap_skill_gap_data") or {}
    matched = kwargs.get("matched_skills") or skill_gap.get("matched_skills", [])
    unverified = (
        kwargs.get("unverified_claims")
        or kwargs.get("unverified_skills")
        or skill_gap.get("unverified_claims", [])
    )
    flags = kwargs.get("forensic_flags", [])

    if isinstance(flags, list):
        actionable_flags = [
            f for f in flags
            if (isinstance(f, dict) and f.get("severity") in ["CRITICAL", "WARNING"])
            or isinstance(f, str)
        ]
        flag_count = len(actionable_flags)
    else:
        flag_count = 0

    matched_str = ", ".join(s.upper() for s in matched) if matched else "none of the listed skills"
    unverified_str = ", ".join(s.upper() for s in unverified) if unverified else "none"

    rationale = (
        f"{candidate} received an overall match score of {score}%. "
        f"Checking their resume against their public GitHub projects confirmed real work in: {matched_str}. "
    )

    if unverified:
        rationale += (
            f"However, we could not find public code or setup files for: {unverified_str}. "
        )
    else:
        rationale += "Every skill listed on the resume was backed up by real code on GitHub. "

    if flag_count > 0:
        rationale += (
            f"Our commit history check also found {flag_count} item(s) worth reviewing (such as unusual commit times or bulk uploads)."
        )
    else:
        rationale += "Their commit history looks natural and consistent, with no suspicious upload patterns."

    return rationale