# backend/skill_gap.py

def analyze_skill_gaps(resume_text: str, repositories: list, imported_modules: list) -> dict:
    """
    Performs academic skill-gap analysis by cross-referencing skills claimed in the resume 
    against concrete evidence found in GitHub repositories and static code analysis.
    """
    resume_lower = resume_text.lower()
    
    # Baseline dictionary of trackable technologies and keywords
    known_techs = {
        "python": ["python"],
        "fastapi": ["fastapi"],
        "javascript": ["javascript", "js", "node", "react"],
        "typescript": ["typescript", "ts"],
        "java": ["java", "spring"],
        "docker": ["docker", "container"],
        "sql": ["sql", "postgres", "mysql", "database"]
    }
    
    # 1. Identify skills claimed in the resume text
    claimed_skills = []
    for tech, keywords in known_techs.items():
        if any(kw in resume_lower for kw in keywords):
            claimed_skills.append(tech)
            
    # 2. Gather actual technical evidence from GitHub repo languages and AST imports
    evidenced_languages = [r.get("language", "").lower() for r in repositories if r.get("language")]
    all_evidence_tokens = set(evidenced_languages + [m.lower() for m in imported_modules])
    
    matched_skills = []
    unverified_claims = []
    
    for skill in claimed_skills:
        # Check if evidence exists in repository languages or code imports
        if any(skill in token for token in all_evidence_tokens) or (skill == "python" and imported_modules):
            matched_skills.append(skill)
        else:
            unverified_claims.append(skill)
            
    # Calculate a quantitative match percentage for the thesis evaluation metrics
    match_percentage = round((len(matched_skills) / max(1, len(claimed_skills))) * 100, 2)

    return {
        "claimed_skills": claimed_skills,
        "matched_skills": matched_skills,
        "unverified_claims": unverified_claims,
        "skill_match_percentage": match_percentage
    }
