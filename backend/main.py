# backend/main.py

import time
import io
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader

from backend.github_client import (
    extract_github_username,
    fetch_github_user_data,
    fetch_github_user_repos,
    fetch_repo_telemetry_bundle
)
from backend.auditor import ResumeAuditor
from backend.ast_auditor import analyze_python_code_structure
from backend.cross_language_auditor import analyze_cross_language_code
from backend.skill_gap import analyze_skill_gaps
from backend.xai_explainer import generate_xai_rationale

try:
    from backend.parser import sanitize_pii_text
except ImportError:
    def sanitize_pii_text(raw_text: str) -> str:
        if not raw_text:
            return ""
        text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", raw_text)
        text = re.sub(r"(\+?\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}", "[REDACTED_PHONE]", text)
        return text


app = FastAPI(
    title="VediCode — Resume & GitHub Verification Engine",
    version="2.7.0",
    description="Automated Candidate Skill Verification, Commit History Forensics, Coding Pattern Stylometry, and Group/Solo Project Auditor."
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
        "system": "VediCode — Resume & GitHub Verification Engine"
    }


@app.post("/audit-candidate/{username:path}")
async def audit_candidate_endpoint(
    username: str,
    file: UploadFile = File(...),
    target_role: str = Form(default="")
):
    """
    Complete End-to-End Audit Pipeline with PDF Extraction, Live GitHub Commit Provenance
    Forensics, Coding Pattern Stylometry, Individual vs. Group Project Verification, and Skill Matching.
    """
    start_time = time.perf_counter()
    clean_username = extract_github_username(username)
    print(f"[*] Starting forensic audit for user: {clean_username} with file: {file.filename}")

    try:
        # 1. Read and Extract Resume Content safely in volatile memory
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

        resume_text_snippet = sanitize_pii_text(resume_text_snippet)
        print(f"[*] Resume text extracted ({len(resume_text_snippet)} chars). Fetching GitHub telemetry...")

        # 2. Fetch GitHub User Profile and Public Repositories
        github_profile = await fetch_github_user_data(clean_username)
        repos = await fetch_github_user_repos(clean_username)
        evaluated_repo_count = len(repos)
        print(f"[*] Fetched {evaluated_repo_count} public repositories for {clean_username}.")

        # 3. Fetch Deep Repository Telemetry (Commits, Contributors, Languages, Manifests, Code Files)
        telemetry_bundle = await fetch_repo_telemetry_bundle(clean_username, repos)
        telemetry_bundle["repos_list"] = repos

        # 4. Run Deep Coding Pattern & Line-by-Line Stylometry Analysis (Feature 1)
        all_imported_modules = []
        static_forensic_flags = []
        style_signatures = []
        sample_files = telemetry_bundle.get("sample_code_files", [])

        for code_file in sample_files:
            fname = f"{code_file.get('repo')}/{code_file.get('filename')}"
            content = code_file.get("content", "")
            if fname.lower().endswith(".py"):
                ast_res = analyze_python_code_structure(content, filename=fname)
                all_imported_modules.extend(ast_res.get("imported_modules", []))
                static_forensic_flags.extend(ast_res.get("forensic_flags", []))
                if ast_res.get("style_signature"):
                    style_signatures.append(ast_res["style_signature"])
            elif fname.lower().endswith((".js", ".ts", ".jsx", ".tsx", ".java")):
                ext_lang = "java" if fname.lower().endswith(".java") else "javascript"
                cl_res = analyze_cross_language_code(content, ext_lang, filename=fname)
                static_forensic_flags.extend(cl_res.get("structured_flags", []))
                if cl_res.get("style_signature"):
                    style_signatures.append(cl_res["style_signature"])

        telemetry_bundle["style_signatures"] = style_signatures

        manifest_text_blob = " ".join(telemetry_bundle.get("manifest_contents", {}).values())
        lang_keys_blob = " ".join(telemetry_bundle.get("languages", {}).keys())
        extra_evidence = f"{manifest_text_blob} {lang_keys_blob}"

        # 5. Perform Strict Skill-Gap Analysis
        skill_gap_data = analyze_skill_gaps(
            resume_text=resume_text_snippet,
            repositories=repos,
            imported_modules=all_imported_modules,
            extra_evidence_text=extra_evidence,
            telemetry_bundle=telemetry_bundle
        )
        claimed_skills = skill_gap_data.get("claimed_skills", [])
        matched_skills = skill_gap_data.get("matched_skills", [])
        unverified_claims = skill_gap_data.get("unverified_claims", [])
        print(f"[*] Skill intersection complete. Matched: {matched_skills}, Unverified: {unverified_claims}")

        # 6. Execute ResumeAuditor (Temporal Provenance + Group/Solo Verification + Cross-Repo Patterns)
        auditor = ResumeAuditor(
            extracted_skills=claimed_skills,
            repo_telemetry=telemetry_bundle,
            username=clean_username
        )
        audit_results = auditor.audit()
        project_ownership = audit_results.get("project_ownership", {})

        all_forensic_flags = audit_results.get("forensic_flags", []) + static_forensic_flags

        if github_profile.get("status") == "fallback" and evaluated_repo_count == 0:
            all_forensic_flags.insert(0, {
                "severity": "CRITICAL",
                "category": "GitHub Account Not Found",
                "line": f"@{clean_username}",
                "message": f"We could not find a public GitHub profile for '@{clean_username}' or it has no public repositories."
            })

        critical_errors = [f for f in all_forensic_flags if f.get("severity") == "CRITICAL"]
        warnings = [f for f in all_forensic_flags if f.get("severity") == "WARNING"]
        notices = [f for f in all_forensic_flags if f.get("severity") not in ["CRITICAL", "WARNING"]]

        actionable_flag_count = len(critical_errors) + len(warnings)

        # 7. Compute Final Calibrated Confidence Score
        if not matched_skills or evaluated_repo_count == 0:
            confidence_score = 0.0
            evaluated_repos_to_show = []
        else:
            raw_heuristic_score = audit_results.get("overall_confidence", 0.0)
            crit_penalty = len(critical_errors) * 12.0
            warn_penalty = len(warnings) * 4.0
            confidence_score = round(max(15.0, min(100.0, raw_heuristic_score - crit_penalty - warn_penalty)), 1)
            evaluated_repos_to_show = repos[:8]

        status = "verified" if (confidence_score >= 70.0 and len(critical_errors) < 2) else "unverified"

        # 8. Generate Explainable AI (XAI) Rationale
        xai_rationale = generate_xai_rationale(
            candidate_name=clean_username,
            confidence_score=confidence_score,
            status=status,
            skill_gap_data=skill_gap_data,
            forensic_flags=all_forensic_flags
        )

        execution_time_seconds = round(time.perf_counter() - start_time, 2)

        return {
            "username": clean_username,
            "target_role": target_role.strip() if target_role else "Software Developer",
            "filename": file.filename,
            "status": status,
            "confidence_score": confidence_score,
            "execution_time_seconds": execution_time_seconds,
            "heuristic_breakdown": {
                "s_lang": audit_results.get("language_score", 0.0),
                "s_dep": audit_results.get("dependency_score", 0.0),
                "s_temp": audit_results.get("temporal_score", 0.0),
                "dependency_verified": audit_results.get("dependency_verified", False),
                "manifests_detected": telemetry_bundle.get("dependencies", [])
            },
            "project_ownership_summary": {
                "individual_projects_count": project_ownership.get("individual_projects_count", 0),
                "group_projects_count": project_ownership.get("group_projects_count", 0),
                "files_inspected_for_patterns": len(sample_files)
            },
            "xai_rationale": xai_rationale,
            "skill_gap_analysis": skill_gap_data,
            "repositories_evaluated": evaluated_repo_count,
            "repositories": evaluated_repos_to_show,
            "forensic_audit_summary": {
                "total_flags": actionable_flag_count,
                "critical_errors": critical_errors,
                "warnings": warnings,
                "notices": notices
            }
        }
    except Exception as e:
        print(f"[!] Critical backend audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))