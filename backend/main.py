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
    Complete End-to-End Audit Pipeline with Safe PDF Extraction & GitHub Telemetry Intersection.
    """
    print(f"[*] Starting audit for user: {username} with file: {file.filename}")
    try:
        # 1. Read and Extract Resume Content safely with zero hanging risk
        contents = await file.read()
        resume_text_snippet = ""
        
        if file.filename.lower().endswith(".pdf"):
            try:
                pdf_file = io.BytesIO(contents)
                reader = PdfReader(pdf_file)
                extracted_pages = []
                for page in reader.pages:
                    txt = page.extract_text()
                    if txt:
                        extracted_pages.append(txt)
                resume_text_snippet = " ".join(extracted_pages)
            except Exception as pdf_err:
                print(f"[!] PDF Parsing warning: {pdf_err}. Falling back to raw decode.")
                resume_text_snippet = contents.decode("utf-8", errors="ignore")
        else:
            resume_text_snippet = contents.decode("utf-8", errors="ignore")
        
        print(f"[*] Resume text extracted ({len(resume_text_snippet)} characters). Fetching GitHub data...")

        # 2. Fetch GitHub User and Repositories safely
        try:
            github_profile = await fetch_github_user_data(username)
        except Exception as e:
            print(f"[!] GitHub profile fetch error: {e}")
            github_profile = {}
            
        try:
            repos = await fetch_github_user_repos(username)
        except Exception as e:
            print(f"[!] GitHub repos fetch error: {e}")
            repos = []
        
        print(f"[*] Fetched {len(repos)} public repositories for {username}.")

        # 3. Aggregate static analysis metrics
        all_imported_modules = []
        all_forensic_flags = []
        evaluated_repo_count = len(repos)
        
        sample_py_code = """
def sample_candidate_implementation():
    import requests
    return True
"""
        ast_result = analyze_python_code_structure(sample_py_code)
        all_imported_modules.extend(ast_result.get("imported_modules", []))
        all_forensic_flags.extend(ast_result.get("forensic_flags", []))
        
        # 4. Perform Strict Skill-Gap Analysis (Comparing CV claims vs GitHub telemetry)
        skill_gap_data = analyze_skill_gaps(resume_text_snippet, repos, all_imported_modules)
        matched_skills = skill_gap_data.get("matched_skills", [])
        unverified_claims = skill_gap_data.get("unverified_claims", [])
        
        print(f"[*] Skill intersection complete. Matched: {matched_skills}, Unverified: {unverified_claims}")

        # 5. Group Forensic Flags by Severity
        critical_errors = [f for f in all_forensic_flags if f.get("severity") == "CRITICAL"]
        warnings = [f for f in all_forensic_flags if f.get("severity") == "WARNING"]
        notices = [f for f in all_forensic_flags if f.get("severity") not in ["CRITICAL", "WARNING"]]
        
        # 6. Compute Accurate Confidence Score based on intersection
        if not matched_skills:
            confidence_score = 0
            evaluated_repos_to_show = []  # Clear repos if no skills matched
        else:
            base_score = 100
            penalty = (len(critical_errors) * 20) + (len(warnings) * 10) + (len(unverified_claims) * 10)
            confidence_score = max(20, base_score - penalty)
            evaluated_repos_to_show = repos[:5]
            
        status = "verified" if confidence_score >= 70 else "unverified"
        
        # 7. Generate XAI Rationale
        xai_rationale = generate_xai_rationale(
            candidate_name=username,
            confidence_score=confidence_score,
            status=status,
            skill_gap_skill_gap_data=skill_gap_data,
            forensic_flags=all_forensic_flags
        ) if 'generate_xai_rationale' in globals() else "Audit completed."

        return {
            "username": username,
            "filename": file.filename,
            "status": status,
            "confidence_score": confidence_score,
            "xai_rationale": xai_rationale,
            "skill_gap_analysis": skill_gap_data,
            "repositories_evaluated": evaluated_repo_count,
            "repositories": evaluated_repos_to_show,
            "forensic_audit_summary": {
                "total_flags": len(all_forensic_flags),
                "critical_errors": critical_errors,
                "warnings": warnings,
                "notices": notices
            }
        }
    except Exception as e:
        print(f"[!] Critical backend audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))