# backend/auditor.py

from datetime import datetime, timezone
from typing import List, Dict, Tuple, Any


def _parse_iso_date(date_str: str) -> datetime:
    if not date_str:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


class ResumeAuditor:
    """
    Core heuristic auditor that strictly intersects CV self-declared skill claims
    with live GitHub repository telemetry, dependency manifests, and temporal Git provenance.
    """
    def __init__(self, extracted_skills: List[str], repo_telemetry: Dict, username: str = ""):
        self.extracted_skills = [s.strip().lower() for s in extracted_skills if s]
        self.repo_telemetry = repo_telemetry or {}
        self.username = (username or "").strip()

    def analyze_temporal_provenance(self, commits_data: List[Dict]) -> Tuple[float, List[str]]:
        """
        Analyzes commit histories for timestamp discrepancies, burst velocity,
        bulk code dumps, browser drag-and-drop uploads, and proxy authorship.
        """
        anomalies: List[str] = []
        self.detailed_forensic_flags: List[Dict[str, Any]] = []
        total_commits = len(commits_data)

        if total_commits == 0:
            msg = "No public commit history was found on GitHub to check coding activity."
            anomalies.append(msg)
            self.detailed_forensic_flags.append({
                "severity": "CRITICAL",
                "category": "No Commit History Found",
                "line": "GitHub Profile",
                "message": msg
            })
            return 0.0, anomalies

        timestamp_deltas_hours: List[float] = []
        commit_intervals_seconds: List[float] = []
        previous_date: datetime = None
        previous_repo: str = None

        clock_inversion_count = 0
        large_delta_count = 0
        moderate_delta_count = 0
        web_upload_count = 0
        external_author_count = 0
        identity_split_count = 0
        distinct_author_emails = set()

        target_user_lower = self.username.lower()

        for commit in commits_data:
            sha_short = (commit.get("sha") or "commit")[:7]
            repo_name = commit.get("_repo_name") or "Project"
            commit_url = commit.get("html_url") or commit.get("_repo_url") or ""

            commit_info = commit.get("commit", {})
            message = (commit_info.get("message") or "").strip()
            author_info = commit_info.get("author") or {}
            committer_info = commit_info.get("committer") or {}

            author_name = (author_info.get("name") or "Unknown").strip()
            author_email = (author_info.get("email") or "").strip()
            committer_name = (committer_info.get("name") or "Unknown").strip()
            committer_email = (committer_info.get("email") or "").strip()

            if author_email and "noreply.github.com" not in author_email.lower():
                distinct_author_emails.add(author_email.lower())

            author_date_str = author_info.get("date")
            committer_date_str = committer_info.get("date")

            # 1. Check Browser Drag-and-Drop ("Add files via upload")
            if "add files via upload" in message.lower():
                web_upload_count += 1
                if web_upload_count <= 2:
                    flag_msg = (
                        f"In project '{repo_name}', commit {sha_short} says 'Add files via upload'. "
                        f"This means the files were dragged and dropped using a web browser instead of pushed normally using Git."
                    )
                    self.detailed_forensic_flags.append({
                        "severity": "WARNING",
                        "category": "Files Uploaded via Web Browser",
                        "line": f"Commit {sha_short}",
                        "message": flag_msg,
                        "url": commit_url
                    })

            # 2. Check Author vs. Committer Timestamp Discrepancies (GIT_AUTHOR_DATE vs GIT_COMMITTER_DATE)
            if author_date_str and committer_date_str:
                a_date = _parse_iso_date(author_date_str)
                c_date = _parse_iso_date(committer_date_str)

                signed_delta_seconds = (c_date - a_date).total_seconds()
                abs_delta_hours = abs(signed_delta_seconds) / 3600.0
                timestamp_deltas_hours.append(abs_delta_hours)

                # Negative delta (> 5 mins): Committer date is BEFORE Author date (Clock Manipulation)
                if signed_delta_seconds < -300:
                    clock_inversion_count += 1
                    flag_msg = (
                        f"In project '{repo_name}' (commit {sha_short}), the upload time ({committer_date_str}) is "
                        f"{abs(signed_delta_seconds)/60:.1f} minutes EARLIER than the time the code was written ({author_date_str}). "
                        f"This is unnatural and usually means the computer clock or commit date was manually changed."
                    )
                    anomalies.append(flag_msg)
                    self.detailed_forensic_flags.append({
                        "severity": "CRITICAL",
                        "category": "Unnatural Commit Time (Clock Mismatch)",
                        "line": f"Commit {sha_short}",
                        "message": flag_msg,
                        "url": commit_url
                    })

                # Severe positive delta (> 24 hours): Rebased, cherry-picked, or proxy patch applied late
                elif abs_delta_hours >= 24.0:
                    large_delta_count += 1
                    if large_delta_count <= 3:
                        flag_msg = (
                            f"In project '{repo_name}' (commit {sha_short}), there is a {abs_delta_hours:.1f}-hour gap "
                            f"between when the code was written ({author_date_str}) and when it was pushed ({committer_date_str}). "
                            f"This often happens when old code is copied over, rebased, or written externally before uploading."
                        )
                        anomalies.append(flag_msg)
                        self.detailed_forensic_flags.append({
                            "severity": "CRITICAL",
                            "category": "Large Time Gap Between Writing & Uploading",
                            "line": f"Commit {sha_short}",
                            "message": flag_msg,
                            "url": commit_url
                        })

                # Moderate positive delta (1 hour to 24 hours)
                elif 1.0 <= abs_delta_hours < 24.0:
                    moderate_delta_count += 1
                    if moderate_delta_count <= 2:
                        flag_msg = (
                            f"In project '{repo_name}' (commit {sha_short}), there is a {abs_delta_hours:.1f}-hour delay "
                            f"between writing the code and pushing the commit."
                        )
                        self.detailed_forensic_flags.append({
                            "severity": "WARNING",
                            "category": "Delay Between Writing & Pushing Code",
                            "line": f"Commit {sha_short}",
                            "message": flag_msg,
                            "url": commit_url
                        })

                # Track interval between consecutive commits in the same repo
                if previous_date and (previous_repo == repo_name or previous_repo is None):
                    interval_sec = abs((a_date - previous_date).total_seconds())
                    commit_intervals_seconds.append(interval_sec)

                previous_date = a_date
                previous_repo = repo_name

            # 3. Check Third-Party / Proxy Author Identity
            gh_author = commit.get("author")
            gh_login = (gh_author.get("login") if isinstance(gh_author, dict) else "") or ""
            if target_user_lower and gh_login and gh_login.lower() != target_user_lower and not gh_login.endswith("[bot]"):
                external_author_count += 1
                if external_author_count <= 2:
                    flag_msg = (
                        f"In project '{repo_name}', commit {sha_short} was written by a different GitHub user "
                        f"('@{gh_login}') instead of '@{self.username}'. Someone else may have written this code."
                    )
                    anomalies.append(flag_msg)
                    self.detailed_forensic_flags.append({
                        "severity": "CRITICAL",
                        "category": "Code Written by Another GitHub User",
                        "line": f"Commit {sha_short}",
                        "message": flag_msg,
                        "url": commit_url
                    })

            # Check Author vs Committer name/email split (excluding GitHub web-flow)
            if (
                author_name.lower() != committer_name.lower()
                and committer_name.lower() not in ["github", "unknown"]
                and "noreply.github.com" not in committer_email.lower()
            ):
                identity_split_count += 1
                if identity_split_count <= 2:
                    flag_msg = (
                        f"In project '{repo_name}' (commit {sha_short}), the code was written by '{author_name}' ({author_email}) "
                        f"but uploaded by a different person: '{committer_name}' ({committer_email})."
                    )
                    self.detailed_forensic_flags.append({
                        "severity": "WARNING",
                        "category": "Different Writer and Uploader Names",
                        "line": f"Commit {sha_short}",
                        "message": flag_msg,
                        "url": commit_url
                    })

        # 4. Aggregate Average Timestamp Delta Check
        avg_delta = sum(timestamp_deltas_hours) / len(timestamp_deltas_hours) if timestamp_deltas_hours else 0.0
        if avg_delta > 48.0 and large_delta_count == 0:
            msg = f"Unusual commit timing: On average, there is a {avg_delta:.1f}-hour gap between when code was written and when it was uploaded."
            anomalies.append(msg)
            self.detailed_forensic_flags.append({
                "severity": "CRITICAL",
                "category": "Large Average Commit Time Gap",
                "line": "Commit History",
                "message": msg
            })

        # 5. "Machine-Gun" Burst Commit Cadence Check (< 180 seconds / 3 minutes between commits)
        burst_count = sum(1 for sec in commit_intervals_seconds if 0 < sec < 180.0)
        if (total_commits > 4 and burst_count >= max(2, int(total_commits * 0.35))) or burst_count >= 4:
            msg = (
                f"Unnatural coding speed: {burst_count} commits were pushed within less than 3 minutes of each other. "
                f"Real coding takes time—this usually means an automated script or bulk upload was used."
            )
            anomalies.append(msg)
            self.detailed_forensic_flags.append({
                "severity": "CRITICAL" if burst_count >= 4 else "WARNING",
                "category": "Too Many Commits in a Few Minutes (Burst Commits)",
                "line": f"{burst_count} Fast Commits",
                "message": msg
            })
        elif burst_count >= 1:
            msg = f"Fast commit activity: {burst_count} commit pair(s) were pushed within less than 3 minutes of each other."
            self.detailed_forensic_flags.append({
                "severity": "WARNING",
                "category": "Very Fast Back-to-Back Commits",
                "line": f"{burst_count} Commit Pair(s)",
                "message": msg
            })

        # 6. Web Upload Summary
        if web_upload_count > 0:
            anomalies.append(
                f"Browser file upload detected: {web_upload_count} out of {total_commits} commits were dragged and dropped via the GitHub website."
            )

        # 7. Workstation Identity Fragmentation
        if len(distinct_author_emails) > 2:
            emails_str = ", ".join(list(distinct_author_emails)[:3])
            msg = (
                f"Found {len(distinct_author_emails)} different author email addresses across commits ({emails_str}). "
                f"This can happen if multiple people or different computers pushed code to this account."
            )
            anomalies.append(msg)
            self.detailed_forensic_flags.append({
                "severity": "WARNING",
                "category": "Multiple Email Identities Used in Commits",
                "line": "Git Author Info",
                "message": msg
            })

        # 8. Repository-Level Forensic Checks (Single-Commit Bulk Dumps, Upload-and-Abandon, Forks)
        repos_list = self.repo_telemetry.get("repos_list", [])
        repo_commits_map = self.repo_telemetry.get("repo_commits_map", {})

        if repos_list:
            forked_repos = [r for r in repos_list if r.get("fork")]
            if len(forked_repos) > 0:
                fork_ratio = (len(forked_repos) / len(repos_list)) * 100.0
                if fork_ratio >= 50.0:
                    msg = (
                        f"{len(forked_repos)} out of {len(repos_list)} public repositories ({fork_ratio:.0f}%) are copied (forked) "
                        f"from other people's projects rather than built from scratch."
                    )
                    anomalies.append(msg)
                    self.detailed_forensic_flags.append({
                        "severity": "WARNING",
                        "category": "Mostly Copied (Forked) Projects",
                        "line": f"{len(forked_repos)}/{len(repos_list)} Projects",
                        "message": msg
                    })

            for r in repos_list:
                if r.get("fork"):
                    continue
                rname = r.get("name", "Repo")
                rsize_kb = int(r.get("size", 0))
                r_commits = repo_commits_map.get(rname, [])
                created_str = r.get("created_at")
                pushed_str = r.get("pushed_at")

                # Single-Commit Monolithic Bulk Dump
                if len(r_commits) == 1 and rsize_kb > 15:
                    sha_s = (r_commits[0].get("sha") or "init")[:7]
                    msg = (
                        f"In project '{rname}', the entire codebase ({rsize_kb} KB) was uploaded all at once in a single commit "
                        f"(Commit {sha_s}) with no step-by-step coding history."
                    )
                    anomalies.append(msg)
                    self.detailed_forensic_flags.append({
                        "severity": "CRITICAL",
                        "category": "Entire Project Uploaded in 1 Commit (Bulk Dump)",
                        "line": f"Commit {sha_s}",
                        "message": msg,
                        "url": r.get("html_url", "")
                    })
                elif len(r_commits) == 2 and rsize_kb > 80:
                    msg = (
                        f"Project '{rname}' ({rsize_kb} KB) has only 2 commits in total, which suggests a finished project "
                        f"was uploaded rather than built step-by-step."
                    )
                    anomalies.append(msg)
                    self.detailed_forensic_flags.append({
                        "severity": "WARNING",
                        "category": "Large Project with Only 2 Commits",
                        "line": f"{rname} (2 Commits)",
                        "message": msg,
                        "url": r.get("html_url", "")
                    })

                # Upload-and-Abandon Lifespan (< 15 mins between repo creation and last push)
                if created_str and pushed_str and rsize_kb > 10:
                    c_dt = _parse_iso_date(created_str)
                    p_dt = _parse_iso_date(pushed_str)
                    lifespan_mins = (p_dt - c_dt).total_seconds() / 60.0
                    if 0 <= lifespan_mins < 15.0:
                        msg = (
                            f"Project '{rname}' ({rsize_kb} KB) was created and uploaded within {lifespan_mins:.1f} minutes "
                            f"and was never updated again."
                        )
                        anomalies.append(msg)
                        self.detailed_forensic_flags.append({
                            "severity": "WARNING",
                            "category": "Uploaded Once and Never Updated Again",
                            "line": f"{lifespan_mins:.1f} Mins Active",
                            "message": msg,
                            "url": r.get("html_url", "")
                        })

        # Compute calibrated S_temp score (0.0 to 1.0)
        crit_count = sum(1 for f in self.detailed_forensic_flags if f.get("severity") == "CRITICAL")
        warn_count = sum(1 for f in self.detailed_forensic_flags if f.get("severity") == "WARNING")
        if not self.detailed_forensic_flags and anomalies:
            penalty = len(anomalies) * 0.25
        else:
            penalty = (crit_count * 0.22) + (warn_count * 0.08)

        s_temp = max(0.0, 1.0 - penalty)
        return round(s_temp, 2), anomalies

    def audit(self) -> Dict:
        commits = self.repo_telemetry.get("commits", [])
        languages = self.repo_telemetry.get("languages", {})
        dependencies = self.repo_telemetry.get("dependencies", [])
        manifest_contents = self.repo_telemetry.get("manifest_contents", {})

        # 1. Always run temporal provenance analysis so forensic flags are captured
        s_temp, anomalies = self.analyze_temporal_provenance(commits)
        forensic_flags = getattr(self, "detailed_forensic_flags", [])

        # 2. Determine active GitHub languages and frameworks from byte counts & manifests
        total_bytes = sum(languages.values()) if languages else 1
        manifest_blob = " ".join(manifest_contents.values()).lower()
        dep_names_blob = " ".join(dependencies).lower()

        github_detected_langs = {}
        tracked_techs = [
            "python", "javascript", "typescript", "java", "react",
            "fastapi", "node", "docker", "sql", "flask", "django", "spring"
        ]
        for tech in tracked_techs:
            lang_bytes = sum(v for k, v in languages.items() if tech in k.lower())
            in_manifests = (tech in manifest_blob) or (tech in dep_names_blob)
            if lang_bytes > 0 or in_manifests:
                ratio = (lang_bytes / total_bytes) if (lang_bytes > 0 and total_bytes > 0) else 0.35
                github_detected_langs[tech] = max(0.25, min(1.0, ratio))

        # 3. STRICT INTERSECTION: Only score skills claimed on CV AND present in GitHub
        matched_skills = []
        unverified_claims = []

        for skill in self.extracted_skills:
            is_backed_by_github = (
                any(skill in g_lang or g_lang in skill for g_lang in github_detected_langs.keys())
                or any(skill in dep.lower() for dep in dependencies)
                or (skill in manifest_blob)
            )
            if is_backed_by_github:
                matched_skills.append(skill)
            else:
                unverified_claims.append(skill)

        # Log unverified CV claims as explicit forensic warnings in simple English
        if unverified_claims:
            unv_str = ", ".join(s.upper() for s in unverified_claims)
            forensic_flags.append({
                "severity": "WARNING",
                "category": "Resume Skills Not Found in GitHub Code",
                "line": "Resume vs GitHub",
                "message": f"The resume claims [{unv_str}], but no matching code or project setup files were found in the public GitHub projects."
            })

        dep_verified = any(
            any(target in dep.lower() for target in ["requirements.txt", "package.json", "pom.xml", "pyproject.toml", "build.gradle"])
            for dep in dependencies
        )
        if not dep_verified and commits:
            forensic_flags.append({
                "severity": "WARNING",
                "category": "Missing Project Setup Files",
                "line": "Project Files",
                "message": "No standard dependency files (like requirements.txt, package.json, or pom.xml) were found in the public projects."
            })

        # If no skills claimed on CV or zero intersection with GitHub, score is strictly 0.0%
        if not self.extracted_skills or not matched_skills:
            if self.extracted_skills and not matched_skills:
                forensic_flags.insert(0, {
                    "severity": "CRITICAL",
                    "category": "No Resume Skills Matched on GitHub",
                    "line": "Overall Check",
                    "message": "None of the technical skills listed on the resume could be found in any of the candidate's public GitHub projects."
                })
            return {
                "overall_confidence": 0.0,
                "temporal_score": round(s_temp * 100, 1),
                "language_score": 0.0,
                "dependency_score": 0.0,
                "dependency_verified": False,
                "anomalies": anomalies,
                "forensic_flags": forensic_flags,
                "language_distribution": {},
                "matched_skills": [],
                "unverified_claims": self.extracted_skills
            }

        # 4. Compute multi-factor heuristic scores (S_lang, S_dep, S_temp)
        lang_scores = {lang: github_detected_langs.get(lang, 0.5) for lang in matched_skills}
        match_coverage = len(matched_skills) / max(len(self.extracted_skills), 1)
        avg_lang_presence = sum(lang_scores.values()) / max(len(lang_scores), 1)
        s_lang = min(1.0, (match_coverage * 0.75) + (avg_lang_presence * 0.25))

        s_dep = 1.0 if dep_verified else 0.55

        # Weighted heuristic formula: CS = (0.40 * S_lang) + (0.30 * S_dep) + (0.30 * S_temp)
        overall_confidence = round(((s_lang * 0.40) + (s_dep * 0.30) + (s_temp * 0.30)) * 100, 2)

        return {
            "overall_confidence": overall_confidence,
            "temporal_score": round(s_temp * 100, 1),
            "language_score": round(s_lang * 100, 1),
            "dependency_score": round(s_dep * 100, 1),
            "dependency_verified": dep_verified,
            "anomalies": anomalies,
            "forensic_flags": forensic_flags,
            "language_distribution": lang_scores,
            "matched_skills": matched_skills,
            "unverified_claims": unverified_claims
        }