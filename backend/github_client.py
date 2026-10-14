# backend/github_client.py

import httpx

async def fetch_github_user_data(username: str) -> dict:
    """
    Fetches GitHub user profile details asynchronously via GitHub REST API.
    """
    url = f"https://api.github.com/users/{username}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
    return {"login": username, "status": "fallback"}

async def fetch_github_user_repos(username: str) -> list:
    """
    Fetches public repositories for a given GitHub user asynchronously.
    """
    url = f"https://api.github.com/users/{username}/repos?per_type=public&sort=updated"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            if response.status_code == 200:
                repos = response.json()
                return [{"name": r.get("name"), "html_url": r.get("html_url"), "language": r.get("language")} for r in repos]
        except Exception:
            pass
    return []

def fetch_repository_data(repo_url: str) -> str:
    """
    Fetches source code contents from a raw GitHub or public code file link.
    """
    try:
        if "github.com" in repo_url and not "raw.githubusercontent.com" in repo_url:
            # Convert standard github blob link to raw format if applicable
            repo_url = repo_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            
        import requests
        response = requests.get(repo_url, timeout=5.0)
        if response.status_code == 200:
            return response.text
    except Exception:
        pass
        
    return """
def default_candidate_code():
    # Fallback mock implementation for analysis
    return True
"""