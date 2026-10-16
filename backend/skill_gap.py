# backend/skill_gap.py

import re
from typing import List, Dict, Optional, Any


KNOWN_TECHS = {
    "python": ["python", "py", "pip", "django", "flask", "pandas", "numpy", "tensorflow", "pytorch"],
    "fastapi": ["fastapi", "uvicorn", "starlette", "pydantic"],
    "javascript": ["javascript", "js", "es6", "nodejs", "node.js", "express", "nextjs", "vue", "angular", "jquery"],
    "react": ["react", "reactjs", "react.js", "react native", "jsx", "tsx"],
    "typescript": ["typescript", "ts-node"],
    "java": ["java", "spring", "springboot", "spring-boot", "maven", "gradle", "hibernate", "jsp", "servlet"],
    "html/css": ["html", "html5", "css", "css3", "tailwind", "tailwindcss", "bootstrap", "sass", "scss"],
    "php": ["php", "laravel", "symfony", "codeigniter", "wordpress"],
    "c#/.net": ["c#", "csharp", ".net", "dotnet", "asp.net"],
    "c/c++": ["c++", "cpp", "clang"],
    "mobile": ["flutter", "dart", "kotlin", "swift", "android", "ios"],
    "docker": ["docker", "dockerfile", "docker-compose", "kubernetes", "k8s", "containerization"],
    "aws/cloud": ["aws", "azure", "gcp", "cloud", "firebase", "vercel", "heroku"],
    "sql": ["sql", "postgres", "postgresql", "mysql", "sqlite", "mongodb", "nosql", "oracle", "mariadb", "sqlalchemy"]
}


def analyze_skill_gaps(
    resume_text: str,
    repositories: list,
    imported_modules: list,
    extra_evidence_text: Optional[str] = "",
    telemetry_bundle: Optional[Dict[str, Any]] = None
) -> dict:
    """
    Performs precise skill-gap analysis using whole-word boundary checks
    and builds direct clickable evidence links (Repository URL, Dependency File URL,
    and Commit Hash URL) for every verified skill.
    """
    resume_lower = resume_text.lower() if resume_text else ""

    # 1. Identify explicitly claimed skills using whole-word regex matching
    claimed_skills = []
    for tech, keywords in KNOWN_TECHS.items():
        all_terms = [tech] + keywords
        is_claimed = any(
            re.search(r'(?:^|[\s,;/()\[\]\-|•])' + re.escape(term) + r'(?:$|[\s,;/()\[\]\-.|•])', resume_lower)
            for term in all_terms
        )
        if is_claimed:
            claimed_skills.append(tech)

    # 2. Gather actual technical evidence from GitHub repos, imports, and manifests
    repo_languages = [str(r.get("language", "")).lower() for r in repositories if r.get("language")]
    repo_text_blob = " ".join([
        f"{r.get('name', '')} {r.get('description', '')} {r.get('language', '')}".lower()
        for r in repositories
    ])
    if extra_evidence_text:
        repo_text_blob += " " + extra_evidence_text.lower()

    all_evidence_tokens = set(repo_languages + [str(m).lower() for m in imported_modules if m])

    matched_skills = []
    unverified_claims = []
    skill_evidence_map: Dict[str, Dict[str, str]] = {}

    repo_commits_map = (telemetry_bundle or {}).get("repo_commits_map", {})
    repo_languages_map = (telemetry_bundle or {}).get("repo_languages_map", {})
    manifest_contents = (telemetry_bundle or {}).get("manifest_contents", {})
    manifest_links = (telemetry_bundle or {}).get("manifest_links", {})

    # 3. Strict Comparison Intersection & Direct Evidence Linking
    for skill in claimed_skills:
        related_terms = [skill] + KNOWN_TECHS.get(skill, [])
        has_repo_match = any(
            re.search(r'\b' + re.escape(term) + r'\b', repo_text_blob)
            or any(term in token for token in all_evidence_tokens)
            for term in related_terms
        )

        if has_repo_match:
            matched_skills.append(skill)
            best_repo_name = ""
            best_repo_url = ""
            best_commit_sha = ""
            best_commit_url = ""
            best_manifest_name = ""
            best_manifest_url = ""

            for r in repositories:
                rname = r.get("name", "")
                rurl = r.get("html_url", "")
                rlang = str(r.get("language") or "").lower()
                rdesc = f"{rname} {r.get('description') or ''} {rlang}".lower()
                rlangs_dict = {k.lower(): v for k, v in repo_languages_map.get(rname, {}).items()}

                repo_matches_skill = (
                    skill in rlang
                    or any(t in rlang for t in related_terms)
                    or any(t in rlangs_dict for t in related_terms)
                    or any(t in rdesc for t in related_terms)
                )

                for m_key, m_body in manifest_contents.items():
                    if m_key.startswith(f"{rname}/"):
                        if any(t in m_body.lower() for t in related_terms) or repo_matches_skill:
                            repo_matches_skill = True
                            if not best_manifest_url:
                                best_manifest_name = m_key
                                best_manifest_url = manifest_links.get(m_key, rurl)

                if repo_matches_skill and not best_repo_url:
                    best_repo_name = rname
                    best_repo_url = rurl
                    r_commits = repo_commits_map.get(rname, [])
                    if r_commits:
                        best_commit_sha = (r_commits[0].get("sha") or "")[:7]
                        best_commit_url = r_commits[0].get("html_url") or rurl

            if not best_repo_url and repositories:
                best_repo_name = repositories[0].get("name", "Repository")
                best_repo_url = repositories[0].get("html_url", "#")
                r_commits = repo_commits_map.get(best_repo_name, [])
                if r_commits:
                    best_commit_sha = (r_commits[0].get("sha") or "")[:7]
                    best_commit_url = r_commits[0].get("html_url") or best_repo_url

            skill_evidence_map[skill] = {
                "repo_name": best_repo_name,
                "repo_url": best_repo_url,
                "commit_sha": best_commit_sha,
                "commit_url": best_commit_url,
                "manifest_name": best_manifest_name,
                "manifest_url": best_manifest_url
            }
        else:
            unverified_claims.append(skill)

    total_claimed = len(claimed_skills)
    match_percentage = round((len(matched_skills) / total_claimed) * 100, 2) if total_claimed > 0 else 0.0

    repository_status_message = (
        "Repositories verified successfully."
        if matched_skills
        else "No skills matched between resume and repositories."
    )

    return {
        "claimed_skills": claimed_skills,
        "matched_skills": matched_skills,
        "unverified_claims": unverified_claims,
        "skill_match_percentage": match_percentage,
        "skill_evidence_map": skill_evidence_map,
        "repository_status_message": repository_status_message
    }