from datetime import datetime
from typing import List, Dict, Tuple

class ResumeAuditor:
    """
    Core heuristic auditor that cross-references extracted resume skill claims
    with live GitHub repository metadata, dependency manifests, and temporal forensics.
    """
    def __init__(self, extracted_skills: List[str], repo_telemetry: Dict):
        self.extracted_skills = [s.lower() for s in extracted_skills]
        self.repo_telemetry = repo_telemetry

    def analyze_temporal_provenance(self, commits_data: List[Dict]) -> Tuple[float, List[str]]:
        """
        Analyzes GitHub commit telemetry for temporal forensics and provenance anomalies:
        1. Author vs. Committer timestamp discrepancies (GIT_AUTHOR_DATE vs. GIT_COMMITTER_DATE)
        2. Commit cadence velocity anomalies (detecting bulk 'machine-gun' code drops)
        """
        anomalies: List[str] = []
        total_commits = len(commits_data)
        
        if total_commits == 0:
            return 0.0, ["No commit history found for temporal forensic analysis."]

        timestamp_deltas: List[float] = []
        commit_intervals: List[float] = []
        previous_date: datetime = None

        for commit in commits_data:
            commit_info = commit.get("commit", {})
            author_info = commit_info.get("author", {})
            committer_info = commit_info.get("committer", {})
            
            author_date_str = author_info.get("date")
            committer_date_str = committer_info.get("date")
            
            if author_date_str and committer_date_str:
                # Parse ISO 8601 timestamps
                a_date = datetime.fromisoformat(author_date_str.replace("Z", "+00:00"))
                c_date = datetime.fromisoformat(committer_date_str.replace("Z", "+00:00"))
                
                # Calculate discrepancy delta in hours (GIT_AUTHOR_DATE vs GIT_COMMITTER_DATE)
                delta_hours = abs((c_date - a_date).total_seconds()) / 3600.0
                timestamp_deltas.append(delta_hours)
                
                if previous_date:
                    interval_hours = abs((a_date - previous_date).total_seconds()) / 3600.0
                    commit_intervals.append(interval_hours)
                previous_date = a_date

        # 1. Evaluate Timestamp Discrepancy Anomalies
        avg_delta = sum(timestamp_deltas) / len(timestamp_deltas) if timestamp_deltas else 0.0
        if avg_delta > 48.0:
            anomalies.append(f"Significant author-committer timestamp discrepancy detected (Average delta: {avg_delta:.1f} hours)[cite: 12].")

        # 2. Evaluate Rapid Burst / 'Machine-Gun' Commit Cadence Anomalies
        burst_count = sum(1 for interval in commit_intervals if interval < 0.05) # under 3 minutes apart
        if total_commits > 5 and burst_count > (total_commits * 0.4):
            anomalies.append("Temporal velocity anomaly detected: High frequency of rapid-succession commits indicative of automated or bulk code imports[cite: 12].")

        # Compute normalized temporal score (S_temp)
        penalty = len(anomalies) * 0.30
        s_temp = max(0.0, 1.0 - penalty)
        
        return round(s_temp, 2), anomalies

    def audit(self) -> Dict:
        """
        Executes the complete heuristic evaluation pipeline:
        - Language distribution analysis (S_lang)
        - Dependency manifest verification (S_dep)
        - Temporal provenance and forensic analysis (S_temp)
        """
        commits = self.repo_telemetry.get("commits", [])
        languages = self.repo_telemetry.get("languages", {})
        dependencies = self.repo_telemetry.get("dependencies", [])

        # 1. Temporal Provenance Score (S_temp) & Anomalies
        s_temp, anomalies = self.analyze_temporal_provenance(commits)

        # 2. Language Distribution Score (S_lang)
        total_bytes = sum(languages.values()) if languages else 1
        lang_scores = {}
        for lang in ["python", "javascript", "java"]:
            lang_bytes = sum(v for k, v in languages.items() if lang in k.lower())
            lang_scores[lang] = lang_bytes / total_bytes if total_bytes > 0 else 0.0

        # 3. Dependency Manifest Verification Score (S_dep)
        dep_verified = any(any(target in dep.lower() for target in ["requirements.txt", "package.json", "pom.xml"]) for dep in dependencies)
        s_dep = 1.0 if dep_verified else 0.5

        # 4. Aggregate Confidence Score Calculation (%)
        avg_lang_score = sum(lang_scores.values()) / max(len(lang_scores), 1)
        overall_confidence = round((avg_lang_score * 0.4 + s_dep * 0.3 + s_temp * 0.3) * 100, 2)

        return {
            "overall_confidence": overall_confidence,
            "temporal_score": s_temp,
            "dependency_verified": dep_verified,
            "anomalies": anomalies,
            "language_distribution": lang_scores
        }