# backend/xai_explainer.py

def generate_xai_rationale(candidate_name: str, confidence_score: int, status: str, skill_gap_data: dict, forensic_flags: list) -> str:
    """
    Generates a natural-language Explainable AI (XAI) rationale incorporating 
    structured severity counts from forensic code analysis.
    """
    matched = skill_gap_data.get("matched_skills", [])
    unverified = skill_gap_data.get("unverified_claims", [])
    match_pct = skill_gap_data.get("skill_match_percentage", 0.0)
    
    rationale_parts = []
    
    # Core Verdict Sentence
    if status == "verified":
        rationale_parts.append(f"Candidate {candidate_name} has been **VERIFIED** with a confidence score of {confidence_score}/100.")
    else:
        rationale_parts.append(f"Candidate {candidate_name} has been **FLAGGED** for review with a confidence score of {confidence_score}/100.")
        
    # Skill-Gap Integration
    if matched:
        rationale_parts.append(f"Technical artifacts successfully verified claimed proficiencies in: {', '.join(matched)} ({match_pct}% skill match rate).")
    if unverified:
        rationale_parts.append(f"Discrepancy detected: The resume claims expertise in [{', '.join(unverified)}], but insufficient code evidence was found.")
        
    # Structured Forensic Count Breakdown
    critical_count = sum(1 for f in forensic_flags if isinstance(f, dict) and f.get("severity") == "CRITICAL")
    warning_count = sum(1 for f in forensic_flags if isinstance(f, dict) and f.get("severity") == "WARNING")
    
    if critical_count > 0 or warning_count > 0:
        rationale_parts.append(f"Static code analysis flagged {critical_count} critical issue(s) and {warning_count} warning(s) requiring technical evaluation."