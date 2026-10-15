# backend/skill_gap.py

import re

def analyze_skill_gaps(resume_text: str, repositories: list, imported_modules: list) -> dict:
    """
    Performs precise skill-gap analysis using strict whole-word boundary checks
    to prevent false positives (like phantom TypeScript claims).
    """
    resume_lower = resume_text.lower() if resume_text else ""
    
    # Controlled dictionary with exact standalone keywords
    known_techs = {
        "python": ["python", "flask", "django", "fastapi"],
        "fastapi": ["fastapi", "uvicorn", "pydantic"],
        "javascript": ["javascript", "react", "node.js", "express", "vue", "angular"],
        "typescript": ["typescript"],
        "java": ["java", "spring", "springboot", "maven"],
        "docker": ["docker", "kubernetes", "k8s"],
        "sql": ["sql", "postgres", "postgresql", "mysql", "mongodb"]
    }
    
    # 1. Identify explicitly claimed skills using whole-word regex matching
    claimed_skills = []
    for tech, keywords in known_techs.items():
        # Check if the technology name or any keyword appears as a distinct word in the resume text
        all_terms = [tech] + keywords
        is_claimed = any(re.search(r'\b' + re.escape(term) + r'\b', resume_lower) for term in all_terms)
        if is_claimed:
            claimed_skills.append(tech)
            
    # 2. Gather actual technical evidence from GitHub repos
    repo_languages = [str(r.get("language", "")).lower() for r in repositories if r.get("language")]
    repo_text_blob = " ".join([f"{r.get('name', '')} {r.get('description', '')}".lower() for r in repositories])
    all_evidence_tokens = set(repo_languages + [m.lower() for m in imported_modules])

    matched_skills = []
    unverified_claims = []
    
    # 3. Strict Comparison Intersection
    for skill in claimed_skills:
        has_repo_match = skill in repo_text_blob or any(skill in token for token in all_evidence_tokens)
        
        if has_repo_match:
            matched_skills.append(skill)
        else:
            unverified_claims.append(skill)
            
    total_claimed = len(claimed_skills)
    match_percentage = round((len(matched_skills) / total_claimed) * 100, 2) if total_claimed > 0 else 0.0

    repository_status_message = "Repositories verified successfully." if matched_skills else "No skills matched between resume and repositories."

    return {
        "claimed_skills": claimed_skills,
        "matched_skills": matched_skills,
        "unverified_claims": unverified_claims,
        "skill_match_percentage": match_percentage,
        "repository_status_message": repository_status_message
    }