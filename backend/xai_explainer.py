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
                status = "Verified (Strong Telemetry)"
            elif score > 0.0:
                status = "Partial Evidence (Low Code Volume)"
                recommendations.append(f"Contribute more frequent code commits utilizing {lang.capitalize()} to strengthen portfolio verification.")
            else:
                status = "Unclaimed / Unverified"
                if lang in self.extracted_skills:
                    recommendations.append(f"Skill inflation detected: '{lang.capitalize()}' is listed on resume but lacks repository byte-count or dependency support.")

            skill_breakdown[lang] = {
                "status": status,
                "confidence_weight": round(score * 100, 2)
            }

        if not dep_verified:
            recommendations.append("Add explicit dependency manifest files (e.g., requirements.txt, package.json, pom.xml) to validate library usage.")

        if anomalies:
            recommendations.append("Resolve temporal anomalies by maintaining consistent development cadences and avoiding bulk-dump commits.")

        return {
            "skill_verification_breakdown": skill_breakdown,
            "upskilling_recommendations": recommendations,
            "forensic_warning_flags": anomalies
        }


def generate_xai_rationale(*args, **kwargs) -> str:
    candidate = kwargs.get("candidate_name", "The candidate")
    score = kwargs.get("confidence_score", kwargs.get("score", "N/A"))
    matched = kwargs.get("matched_skills", [])
    unverified = kwargs.get("unverified_claims", kwargs.get("unverified_skills", []))
    flags = kwargs.get("forensic_flags", [])

    matched_str = ", ".join(matched) if matched else "none of the primary target languages"
    unverified_str = ", ".join(unverified) if unverified else "none"
    flag_count = len(flags) if isinstance(flags, list) else 0

    rationale = f"Audit evaluation for {candidate} yielded an overall confidence score of {score}%. Cross-referencing the resume against public GitHub telemetry positively verified [{matched_str}]. "

    if unverified:
        rationale += f"However, potential resume inflation or missing artifact evidence was noted for [{unverified_str}], which lacked sufficient repository byte-count or manifest declarations. "
    else:
        rationale += "All declared core technical competencies were backed by repository evidence. "

    if flag_count > 0:
        rationale += f"Additionally, the forensic analyzer raised {flag_count} warning/anomaly flag(s) during codebase and temporal provenance inspection."
    else:
        rationale += "Zero critical forensic or temporal anomalies were detected across the evaluated commit history."

    return rationale