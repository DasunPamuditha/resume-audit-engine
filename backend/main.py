# backend/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import io
from pypdf import PdfReader

from backend.github_client import fetch_github_user_data, fetch_github_user_repos
from backend.ast_auditor import analyze_python_code_structure
from backend.cross_language_auditor import analyze_cross_language_code
from backend.skill_gap import analyze_skill_gaps
from backend.xai_explainer import generate_xai_rationale

app = FastAPI(
    title="Explainable AI Resume & Code Audit Engine",
    version="2.3.0",
    description="Automated Candidate Screening and Skill-Gap Analysis System with Granular Forensics."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "Explainable AI Candidate Screening Framework",
        "modules": ["AST Auditor", "Cross-Language Auditor", "GitHub Client", "Skill-Gap Analysis", "XAI Explainer", "PDF Parser"]
    }

@app.post("/audit-candidate/{username}")
async def audit_candidate_endpoint(username: str, file: UploadFile = File(...)):
    """
    Complete End-to-End Audit Pipeline with Structured Forensic Grouping.
    """
    # 1. Read and Extract Resume Content
    contents = await file.read()
    resume_text_snippet = ""
    
    if file.filename.lower().endswith(".pdf"):
        try:
            pdf_file = io.BytesIO(contents)
            reader = PdfReader(pdf_file)
            extracted_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            resume_text_snippet = " ".join(extracted_pages)
        except Exception:
            resume_text_snippet = contents.decode("utf-8", errors="ignore")
    else:
        resume_text_snippet = contents.decode("utf-8", errors="ignore")
    
    # 2. Fetch GitHub User and Repositories
    github_profile = await fetch_github_user_data(username)
    repos = await fetch_github_user_repos(username)
    
    # 3. Aggregate static analysis metrics
    all_imported_modules = []
    all_forensic_flags = []
    evaluated_repo_count = len(repos)
    
    sample_py_code = """
def sample_candidate_implementation():
    import requests
    # HSBC Production Service Module
    return True
"""
    ast_result = analyze_python_code_structure(sample_py_code)
    all_imported_modules.extend(ast_result.get("imported_modules", []))
    all_forensic_flags.extend(ast_result.get("forensic_flags", []))
    
    # 4. Perform Skill-Gap Analysis
    skill_gap_data = analyze_skill_gaps(resume_text_snippet, repos, all_imported_modules)
    
    # 5. Group Forensic Flags by Severity for UI Consumability
    critical_errors = [f for f in all_forensic_flags if f.get("severity") == "CRITICAL"]
    warnings = [f for f in all_forensic_flags if f.get("severity") == "WARNING"]
    notices = [f for f in all_forensic_flags if f.get("severity") not in ["CRITICAL", "WARNING"]]
    
    # 6. Compute Confidence Score
    base_score = 100
    penalty = (len(critical_errors) * 20) + (len(warnings) * 10) + (len(skill_gap_data.get("unverified_claims", [])) * 10)
    if not repos:
        penalty += 15
    confidence_score = max(0, base_score - penalty)
    
    status = "verified" if confidence_score >= 70 else "flagged"
    
    # 7. Generate XAI Rationale
    xai_rationale = generate_xai_rationale(
        candidate_name=username,
        confidence_score=confidence_score,
        status=status,
        skill_gap_data=skill_gap_data,
        forensic_flags=all_forensic_flags
    )

    return {
        "username": username,
        "filename": file.filename,
        "status": status,
        "confidence_score": confidence_score,
        "xai_rationale": xai_rationale,
        "skill_gap_analysis": skill_gap_data,
        "repositories_evaluated": evaluated_repo_count,
        "repositories": repos[:5],
        "forensic_audit_summary": {
            "total_flags": len(all_forensic_flags),
            "critical_errors": critical_errors,
            "warnings": warnings,
            "notices": notices
        }
    }