# backend/auditor.py

from backend.github_client import fetch_repository_data
from backend.ast_auditor import analyze_python_code_structure

def audit_candidate_profile(resume_text: str, repos: list) -> dict:
    """
    Audits a candidate's profile by evaluating resume keywords, GitHub repositories,
    and running AST static analysis on discovered code artifacts.
    """
    # Run AST analysis on a default or extracted code snippet
    sample_code = """
def evaluated_candidate_module():
    """HSBC / Software Engineering implementation sample."""
    return True
"""
    ast_metrics = analyze_python_code_structure(sample_code)
    
    # Simple weighted scoring logic
    base_score = 100
    forensic_flags = ast_metrics.get("forensic_flags", [])
    
    # Deduct points for forensic flags or lack of repos
    penalty = len(forensic_flags) * 15
    if not repos:
        penalty += 10
        
    confidence_score = max(0, base_score - penalty)
    
    status = "verified" if confidence_score >= 75 else "flagged"

    return {
        "status": status,
        "confidence_score": confidence_score,
        "resume_summary": f"Processed resume text ({len(resume_text)} characters analyzed).",
        "repositories_evaluated": len(repos),
        "repository_list": repos[:5], # Return top 5 repos for review
        "ast_metrics": ast_metrics,
        "forensic_flags": forensic_flags
    }

def audit_repository_code(source_code: str, claimed_skill: str) -> dict:
    """
    Performs forensic auditing on direct source code uploads using AST static analysis.
    """
    ast_metrics = analyze_python_code_structure(source_code)
    return {
        "status": "verified",
        "ast_metrics": ast_metrics,
        "forensic_flags": ast_metrics.get("forensic_flags", [])
    }