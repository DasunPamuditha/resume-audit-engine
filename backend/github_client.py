# backend/github_client.py

import os
import httpx
import requests

# Optional GitHub Token support to prevent rate-limiting (5000 requests/hour vs 60 unauthenticated)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

HEADERS = {
    "User-Agent": "VediCode-Resume-Audit-Engine",
    "Accept": "application/vnd.github.v3+json"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

async def fetch_github_user_data(username: str) -> dict:
    """
    Fetches GitHub user profile details asynchronously via GitHub REST API.
    """
    url = f"https://api.github.com/users/{username}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=HEADERS, timeout=10.0)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[!] GitHub User API warning for {username}: Status {response.status_code}")
        except Exception as e:
            print(f"[!] GitHub User API exception for {username}: {e}")
    return {"login": username, "status": "fallback"}

async def fetch_github_user_repos(username: str) -> list:
    """
    Fetches public repositories for a given GitHub user asynchronously with rate-limit protection.
    """
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=HEADERS, timeout=12.0)
            if response.status_code == 200:
                repos = response.json()
                print(f"[*] Successfully fetched {len(repos)} repositories for @{username}")
                return [{
                    "name": r.get("name"), 
                    "html_url": r.get("html_url"), 
                    "language": r.get("language"), 
                    "stargazers_count": r.get("stargazers_count", 0), 
                    "description": r.get("description", "")
                } for r in repos]
            else:
                print(f"[!] GitHub Repos API error for {username}: Status {response.status_code} - {response.text}")
        except Exception as e:
            print(f"[!] GitHub Repos API exception for {username}: {e}")
    return []

def fetch_repository_data(repo_url: str) -> str:
    """
    Fetches source code contents from a raw GitHub or public code file link.
    """
    try:
        if "github.com" in repo_url and not "raw.githubusercontent.com" in repo_url:
            repo_url = repo_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            
        response = requests.get(repo_url, headers=HEADERS, timeout=5.0)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"[!] Fetch repository data exception: {e}")
        
    return """
def default_candidate_code():
    return True
"""