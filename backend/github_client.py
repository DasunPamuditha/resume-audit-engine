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
                repos = respons