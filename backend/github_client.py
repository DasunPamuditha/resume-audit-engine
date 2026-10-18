# backend/github_client.py

import os
import re
import json
import time
import html
import asyncio
import httpx
import requests
from typing import Dict, List, Any

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

HEADERS = {
    "User-Agent": "VediCode-Resume-Audit-Engine",
    "Accept": "application/vnd.github.v3+json"
}

WEB_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

MANIFEST_FILENAMES = {
    "requirements.txt",
    "pyproject.toml",
    "pipfile",
    "setup.py",
    "package.json",
    "pom.xml",
    "build.gradle",
    "dockerfile",
    "docker-compose.yml"
}

CODE_EXTENSIONS = (".py", ".js", ".ts", ".jsx", ".tsx", ".java")

# Persistent Disk Cache (v3 includes contributors & deep folder file trees)
CACHE_FILE = os.path.join(os.path.dirname(__file__), ".vedicode_cache_v3.json")
CACHE_TTL_SECONDS = 7200  # 2 hours


def _load_disk_cache() -> Dict[str, Any]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"users": {}, "repos": {}, "telemetry": {}}


def _save_disk_cache(cache_data: Dict[str, Any]) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
    except Exception:
        pass


_DISK_CACHE = _load_disk_cache()


def extract_github_username(raw_input: str) -> str:
    cleaned = (raw_input or "").strip()
    if "github.com/" in cleaned.lower():
        match = re.search(r"github\.com/([a-zA-Z0-9\-_]+)", cleaned, re.IGNORECASE)
        if match:
            return match.group(1)
    return cleaned.strip("/").split("/")[0]


async def _scrape_github_repos_fallback(username: str) -> List[Dict[str, Any]]:
    url = f"https://github.com/{username}?tab=repositories"
    repos_list: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=WEB_HEADERS, timeout=12.0)
            if resp.status_code != 200:
                return []
            page_html = resp.text

            pattern = re.compile(
                rf'<a[^>]+href="/{re.escape(username)}/([^/"?#]+)"[^>]*itemprop="name codeRepository"[^>]*>',
                re.IGNORECASE
            )
            matches = list(pattern.finditer(page_html))
            seen_names = set()

            for idx, m in enumerate(matches):
                repo_name = m.group(1).strip()
                if repo_name.lower() in seen_names:
                    continue
                seen_names.add(repo_name.lower())

                start_pos = m.start()
                end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else start_pos + 3000
                block = page_html[start_pos:end_pos]

                lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>\s*([^<\n]+)\s*<', block)
                language = html.unescape(lang_match.group(1).strip()) if lang_match else None

                desc_match = re.search(r'itemprop="description"[^>]*>\s*([\s\S]*?)\s*</p>', block)
                description = html.unescape(re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()) if desc_match else ""

                time_match = re.search(r'datetime="([^"]+)"', block)
                pushed_at = time_match.group(1) if time_match else None

                is_fork = "Forked from" in block

                repos_list.append({
                    "name": repo_name,
                    "html_url": f"https://github.com/{username}/{repo_name}",
                    "language": language,
                    "stargazers_count": 0,
                    "description": description,
                    "fork": is_fork,
                    "size": 120,
                    "created_at": None,
                    "pushed_at": pushed_at,
                    "updated_at": pushed_at,
                    "default_branch": "HEAD",
                    "has_issues": True,
                })
            print(f"[*] Fallback web scraper fetched {len(repos_list)} repositories for @{username}")
        except Exception as e:
            print(f"[!] Fallback repo scrape exception for {username}: {e}")

    return repos_list


async def _fetch_commits_atom_fallback(
    client: httpx.AsyncClient, username: str, repo_name: str, repo_html_url: str
) -> List[Dict[str, Any]]:
    atom_urls = [
        f"https://github.com/{username}/{repo_name}/commits.atom",
        f"https://github.com/{username}/{repo_name}/commits/main.atom",
        f"https://github.com/{username}/{repo_name}/commits/master.atom",
    ]
    for url in atom_urls:
        try:
            resp = await client.get(url, headers=WEB_HEADERS, timeout=6.0, follow_redirects=True)
            if resp.status_code == 200 and "<entry>" in resp.text:
                entries = re.findall(r"<entry>([\s\S]*?)</entry>", resp.text)
                commits = []
                for entry in entries[:25]:
                    sha_m = re.search(r"Commit/([0-9a-fA-F]{7,40})", entry)
                    sha = sha_m.group(1) if sha_m else "commit"

                    title_m = re.search(r"<title[^>]*>([\s\S]*?)</title>", entry)
                    msg = html.unescape(title_m.group(1).strip()) if title_m else "Commit"

                    updated_m = re.search(r"<updated>([^<]+)</updated>", entry)
                    date_str = updated_m.group(1).strip() if updated_m else None

                    name_m = re.search(r"<author>\s*<name>([^<]+)</name>", entry)
                    author_name = html.unescape(name_m.group(1).strip()) if name_m else username

                    uri_m = re.search(r"<uri>https://github\.com/([^/<]+)</uri>", entry)
                    author_login = uri_m.group(1).strip() if uri_m else username

                    commits.append({
                        "sha": sha,
                        "html_url": f"{repo_html_url}/commit/{sha}",
                        "_repo_name": repo_name,
                        "_repo_url": repo_html_url,
                        "author": {"login": author_login},
                        "commit": {
                            "message": msg,
                            "author": {
                                "name": author_name,
                                "email": f"{author_login.lower()}@users.noreply.github.com",
                                "date": date_str
                            },
                            "committer": {
                                "name": author_name,
                                "email": f"{author_login.lower()}@users.noreply.github.com",
                                "date": date_str
                            }
                        }
                    })
                if commits:
                    return commits
        except Exception:
            pass
    return []


async def fetch_github_user_data(username: str) -> dict:
    clean_user = extract_github_username(username)
    cache_key = clean_user.lower()

    cached_entry = _DISK_CACHE.get("users", {}).get(cache_key)
    if cached_entry and (time.time() - cached_entry.get("ts", 0) < CACHE_TTL_SECONDS):
        return cached_entry["data"]

    url = f"https://api.github.com/users/{clean_user}"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, headers=HEADERS, timeout=8.0)
            if response.status_code == 200:
                data = response.json()
                _DISK_CACHE.setdefault("users", {})[cache_key] = {"ts": time.time(), "data": data}
                _save_disk_cache(_DISK_CACHE)
                return data
            elif response.status_code == 403:
                web_resp = await client.get(f"https://github.com/{clean_user}", headers=WEB_HEADERS, timeout=8.0)
                if web_resp.status_code == 200:
                    data = {"login": clean_user, "status": "ok_web_fallback"}
                    _DISK_CACHE.setdefault("users", {})[cache_key] = {"ts": time.time(), "data": data}
                    _save_disk_cache(_DISK_CACHE)
                    return data
        except Exception as e:
            print(f"[!] GitHub User API exception for {clean_user}: {e}")

    return {"login": clean_user, "status": "fallback"}


async def fetch_github_user_repos(username: str) -> list:
    clean_user = extract_github_username(username)
    cache_key = clean_user.lower()

    cached_entry = _DISK_CACHE.get("repos", {}).get(cache_key)
    if cached_entry and (time.time() - cached_entry.get("ts", 0) < CACHE_TTL_SECONDS):
        cached_repos = cached_entry.get("data", [])
        if cached_repos:
            print(f"[*] Using cached repositories ({len(cached_repos)}) for @{clean_user}")
            return cached_repos

    url = f"https://api.github.com/users/{clean_user}/repos?per_page=100&sort=updated"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=HEADERS, timeout=10.0)
            if response.status_code == 200:
                repos = response.json()
                print(f"[*] Successfully fetched {len(repos)} repositories via REST API for @{clean_user}")
                parsed_repos = [
                    {
                        "name": r.get("name"),
                        "html_url": r.get("html_url"),
                        "language": r.get("language"),
                        "stargazers_count": r.get("stargazers_count", 0),
                        "description": r.get("description") or "",
                        "fork": bool(r.get("fork", False)),
                        "size": int(r.get("size", 0)),
                        "created_at": r.get("created_at"),
                        "pushed_at": r.get("pushed_at"),
                        "updated_at": r.get("updated_at"),
                        "default_branch": r.get("default_branch", "main"),
                        "has_issues": r.get("has_issues", True),
                    }
                    for r in repos
                    if isinstance(r, dict)
                ]
                if parsed_repos:
                    _DISK_CACHE.setdefault("repos", {})[cache_key] = {"ts": time.time(), "data": parsed_repos}
                    _save_disk_cache(_DISK_CACHE)
                return parsed_repos
            else:
                print(f"[!] GitHub REST API returned {response.status_code} for {clean_user}. Activating Web Fallback...")
        except Exception as e:
            print(f"[!] GitHub Repos API exception for {clean_user}: {e}")

    fallback_repos = await _scrape_github_repos_fallback(clean_user)
    if fallback_repos:
        _DISK_CACHE.setdefault("repos", {})[cache_key] = {"ts": time.time(), "data": fallback_repos}
        _save_disk_cache(_DISK_CACHE)
        return fallback_repos

    if cached_entry:
        return cached_entry.get("data", [])
    return []


async def _scrape_repo_files_web_fallback(
    client: httpx.AsyncClient, username: str, repo_name: str, default_branch: str
) -> List[str]:
    """
    When 403 rate-limited, scrapes the repository's public HTML tree page to discover
    code files (.py, .js, .ts, .java) in root or common subfolders.
    """
    discovered_paths: List[str] = []
    try:
        resp = await client.get(f"https://github.com/{username}/{repo_name}", headers=WEB_HEADERS, timeout=5.0)
        if resp.status_code == 200:
            blob_matches = re.findall(
                rf'href="/{re.escape(username)}/{re.escape(repo_name)}/blob/[^/]+/([^"#?]+)"',
                resp.text
            )
            for path in blob_matches:
                if path.lower().endswith(CODE_EXTENSIONS) and path not in discovered_paths:
                    discovered_paths.append(path)

            # Check common subfolders if no root code files found
            if not discovered_paths:
                tree_matches = re.findall(
                    rf'href="/{re.escape(username)}/{re.escape(repo_name)}/tree/([^/]+)/([^"#?]+)"',
                    resp.text
                )
                for branch_name, folder in tree_matches[:2]:
                    sub_resp = await client.get(
                        f"https://github.com/{username}/{repo_name}/tree/{branch_name}/{folder}",
                        headers=WEB_HEADERS,
                        timeout=4.0
                    )
                    if sub_resp.status_code == 200:
                        sub_blobs = re.findall(
                            rf'href="/{re.escape(username)}/{re.escape(repo_name)}/blob/[^/]+/([^"#?]+)"',
                            sub_resp.text
                        )
                        for spath in sub_blobs:
                            if spath.lower().endswith(CODE_EXTENSIONS) and spath not in discovered_paths:
                                discovered_paths.append(spath)
    except Exception:
        pass
    return discovered_paths[:3]


async def _fetch_single_repo_telemetry(
    client: httpx.AsyncClient, username: str, repo: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Concurrently fetches commits, contributors (for Group vs Individual verification),
    language byte-counts, dependency manifests, and source code files (including subfolders).
    """
    repo_name = repo.get("name", "")
    repo_html_url = repo.get("html_url", f"https://github.com/{username}/{repo_name}")
    default_branch = repo.get("default_branch") or "HEAD"
    base_url = f"https://api.github.com/repos/{username}/{repo_name}"

    commits_url = f"{base_url}/commits?per_page=30"
    langs_url = f"{base_url}/languages"
    contributors_url = f"{base_url}/contributors?per_page=25"
    tree_url = f"{base_url}/git/trees/{default_branch}?recursive=1"

    commits_resp, langs_resp, contrib_resp, tree_resp = await asyncio.gather(
        client.get(commits_url, headers=HEADERS, timeout=6.0),
        client.get(langs_url, headers=HEADERS, timeout=5.0),
        client.get(contributors_url, headers=HEADERS, timeout=5.0),
        client.get(tree_url, headers=HEADERS, timeout=6.0),
        return_exceptions=True
    )

    # 1. Process Commits
    commits = []
    if not isinstance(commits_resp, Exception) and commits_resp.status_code == 200:
        data = commits_resp.json()
        if isinstance(data, list):
            for c in data:
                c["_repo_name"] = repo_name
                c["_repo_url"] = repo_html_url
            commits = data
    else:
        commits = await _fetch_commits_atom_fallback(client, username, repo_name, repo_html_url)

    # 2. Process Languages
    languages = {}
    if not isinstance(langs_resp, Exception) and langs_resp.status_code == 200:
        data = langs_resp.json()
        if isinstance(data, dict):
            languages = data
    elif repo.get("language"):
        languages = {repo["language"]: max(int(repo.get("size", 100)) * 1024, 10240)}

    # 3. Process Contributors (Feature 2: Group vs Individual Project Verification)
    contributors_list = []
    if not isinstance(contrib_resp, Exception) and contrib_resp.status_code == 200:
        c_data = contrib_resp.json()
        if isinstance(c_data, list):
            for c_item in c_data:
                if isinstance(c_item, dict):
                    login_name = str(c_item.get("login") or "")
                    if login_name and not login_name.endswith("[bot]"):
                        contributors_list.append({
                            "login": login_name,
                            "contributions": int(c_item.get("contributions", 1))
                        })

    # Fallback contributor calculation from commit authors if contributors endpoint was rate-limited
    if not contributors_list and commits:
        author_counts: Dict[str, int] = {}
        for c in commits:
            gh_author = c.get("author")
            login = (gh_author.get("login") if isinstance(gh_author, dict) else "") or ""
            if not login:
                commit_author = (c.get("commit") or {}).get("author") or {}
                login = commit_author.get("name") or commit_author.get("email") or "Contributor"
            if login and not str(login).endswith("[bot]"):
                author_counts[login] = author_counts.get(login, 0) + 1
        contributors_list = [{"login": k, "contributions": v} for k, v in author_counts.items()]

    # 4. Process Repository Files & Subdirectories (Feature 1: Deep Code Pattern Inspection)
    manifests_found = []
    manifest_links = {}
    manifest_contents = {}
    sample_code_files = []
    files_to_download = []

    if not isinstance(tree_resp, Exception) and tree_resp.status_code == 200:
        tree_data = tree_resp.json()
        tree_items = tree_data.get("tree", []) if isinstance(tree_data, dict) else []
        for item in tree_items:
            if not isinstance(item, dict) or item.get("type") != "blob":
                continue
            path = (item.get("path") or "").strip()
            fname = path.split("/")[-1]
            fname_lower = fname.lower()
            size_bytes = int(item.get("size") or 0)

            # Skip node_modules, venv, build, dist, or minified files
            if any(skip in path.lower() for skip in ["node_modules/", "venv/", ".venv/", "dist/", "build/", ".min."]):
                continue

            raw_url = f"https://raw.githubusercontent.com/{username}/{repo_name}/{default_branch}/{path}"
            html_file_url = f"{repo_html_url}/blob/{default_branch}/{path}"

            if fname_lower in MANIFEST_FILENAMES:
                manifest_key = f"{repo_name}/{path}"
                manifests_found.append(manifest_key)
                manifest_links[manifest_key] = html_file_url
                files_to_download.append(("manifest", path, repo_name, raw_url, html_file_url))
            elif fname_lower.endswith(CODE_EXTENSIONS) and 30 < size_bytes < 120000:
                files_to_download.append(("code", path, repo_name, raw_url, html_file_url))

        # Prioritize downloading manifests + up to 3 code files per repository
        manifest_downloads = [f for f in files_to_download if f[0] == "manifest"][:2]
        code_downloads = [f for f in files_to_download if f[0] == "code"][:3]
        selected_downloads = manifest_downloads + code_downloads

        if selected_downloads:
            dl_tasks = [client.get(url, timeout=4.5) for _, _, _, url, _ in selected_downloads]
            dl_resps = await asyncio.gather(*dl_tasks, return_exceptions=True)
            for (ftype, path, rname, _, html_url), fresp in zip(selected_downloads, dl_resps):
                if not isinstance(fresp, Exception) and fresp.status_code == 200:
                    if ftype == "manifest":
                        manifest_contents[f"{rname}/{path}"] = fresp.text
                    else:
                        sample_code_files.append({
                            "repo": rname,
                            "filename": path,
                            "html_url": html_url,
                            "content": fresp.text
                        })
    else:
        # Fallback when API is rate-limited: probe raw manifests and scrape web tree for code files
        probe_files = ["package.json", "requirements.txt", "pom.xml"]
        raw_tasks = [
            client.get(f"https://raw.githubusercontent.com/{username}/{repo_name}/HEAD/{pf}", timeout=4.0)
            for pf in probe_files
        ]
        raw_resps = await asyncio.gather(*raw_tasks, return_exceptions=True)
        for pf, r_resp in zip(probe_files, raw_resps):
            if not isinstance(r_resp, Exception) and r_resp.status_code == 200:
                m_key = f"{repo_name}/{pf}"
                manifests_found.append(m_key)
                manifest_links[m_key] = f"{repo_html_url}/blob/HEAD/{pf}"
                manifest_contents[m_key] = r_resp.text

        discovered_code_paths = await _scrape_repo_files_web_fallback(client, username, repo_name, default_branch)
        if discovered_code_paths:
            code_tasks = [
                client.get(f"https://raw.githubusercontent.com/{username}/{repo_name}/HEAD/{cp}", timeout=4.0)
                for cp in discovered_code_paths
            ]
            code_resps = await asyncio.gather(*code_tasks, return_exceptions=True)
            for cp, c_resp in zip(discovered_code_paths, code_resps):
                if not isinstance(c_resp, Exception) and c_resp.status_code == 200:
                    sample_code_files.append({
                        "repo": repo_name,
                        "filename": cp,
                        "html_url": f"{repo_html_url}/blob/HEAD/{cp}",
                        "content": c_resp.text
                    })

    return {
        "repo_name": repo_name,
        "repo_meta": repo,
        "commits": commits,
        "contributors": contributors_list,
        "languages": languages,
        "manifests_found": manifests_found,
        "manifest_links": manifest_links,
        "manifest_contents": manifest_contents,
        "sample_code_files": sample_code_files,
    }


async def fetch_repo_telemetry_bundle(username: str, repos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates deep telemetry across the candidate's repositories concurrently,
    including contributor breakdowns and source code files for stylometric pattern checks.
    """
    clean_user = extract_github_username(username)
    cache_key = clean_user.lower()

    if not repos:
        return {
            "commits": [],
            "repo_commits_map": {},
            "repo_contributors_map": {},
            "repo_languages_map": {},
            "languages": {},
            "dependencies": [],
            "manifest_links": {},
            "manifest_contents": {},
            "sample_code_files": []
        }

    cached_entry = _DISK_CACHE.get("telemetry", {}).get(cache_key)
    if cached_entry and (time.time() - cached_entry.get("ts", 0) < CACHE_TTL_SECONDS):
        cached_bundle = cached_entry.get("data", {})
        if cached_bundle.get("commits") or cached_bundle.get("languages"):
            print(f"[*] Using cached deep telemetry bundle for @{clean_user}")
            return dict(cached_bundle)

    non_fork_repos = [r for r in repos if not r.get("fork")]
    target_repos = (non_fork_repos if non_fork_repos else repos)[:6]

    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [_fetch_single_repo_telemetry(client, clean_user, r) for r in target_repos]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_commits = []
    repo_commits_map = {}
    repo_contributors_map = {}
    repo_languages_map = {}
    aggregate_languages: Dict[str, int] = {}
    all_dependencies = []
    all_manifest_links = {}
    all_manifest_contents = {}
    all_sample_code_files = []

    for res in results:
        if isinstance(res, Exception) or not isinstance(res, dict):
            continue
        rname = res["repo_name"]
        r_commits = res.get("commits", [])
        all_commits.extend(r_commits)
        repo_commits_map[rname] = r_commits
        repo_contributors_map[rname] = res.get("contributors", [])
        repo_languages_map[rname] = res.get("languages", {})

        for lang, byte_count in res.get("languages", {}).items():
            aggregate_languages[lang] = aggregate_languages.get(lang, 0) + int(byte_count)

        all_dependencies.extend(res.get("manifests_found", []))
        all_manifest_links.update(res.get("manifest_links", {}))
        all_manifest_contents.update(res.get("manifest_contents", {}))
        all_sample_code_files.extend(res.get("sample_code_files", []))

    for r in repos:
        lang = r.get("language")
        if lang and lang not in aggregate_languages:
            aggregate_languages[lang] = max(int(r.get("size", 100)) * 1024, 10240)

    bundle = {
        "commits": all_commits,
        "repo_commits_map": repo_commits_map,
        "repo_contributors_map": repo_contributors_map,
        "repo_languages_map": repo_languages_map,
        "languages": aggregate_languages,
        "dependencies": all_dependencies,
        "manifest_links": all_manifest_links,
        "manifest_contents": all_manifest_contents,
        "sample_code_files": all_sample_code_files,
    }

    if all_commits or aggregate_languages:
        _DISK_CACHE.setdefault("telemetry", {})[cache_key] = {"ts": time.time(), "data": bundle}
        _save_disk_cache(_DISK_CACHE)

    return bundle


def fetch_repository_data(repo_url: str) -> str:
    try:
        if "github.com" in repo_url and "raw.githubusercontent.com" not in repo_url:
            repo_url = repo_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        response = requests.get(repo_url, headers=HEADERS, timeout=5.0)
        if response.status_code == 200:
            return response.text
    except Exception as e:
        print(f"[!] Fetch repository data exception: {e}")

    return "def default_candidate_code():\n    return True\n"