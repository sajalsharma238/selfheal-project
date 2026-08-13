"""The pipeline's 'hands' — talks to GitHub's REST API and cleans up logs."""

import re
import subprocess
import requests

API = "https://api.github.com"


class GitHubClient:
    """Reads failed runs and opens pull requests via the GitHub API."""

    def __init__(self, token, repo):
        self.repo = repo  # "owner/name"
        self._s = requests.Session()
        self._s.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def get_run(self, run_id):
        r = self._s.get(f"{API}/repos/{self.repo}/actions/runs/{run_id}")
        r.raise_for_status()
        return r.json()

    def get_failed_jobs(self, run_id):
        r = self._s.get(f"{API}/repos/{self.repo}/actions/runs/{run_id}/jobs")
        r.raise_for_status()
        return [j for j in r.json().get("jobs", []) if j.get("conclusion") == "failure"]

    def get_job_logs(self, job_id, max_chars=40000):
        r = self._s.get(f"{API}/repos/{self.repo}/actions/jobs/{job_id}/logs")
        r.raise_for_status()
        return tail_logs(r.text, max_chars)

    def create_pr(self, head, base, title, body, draft=False):
        r = self._s.post(
            f"{API}/repos/{self.repo}/pulls",
            json={"title": title, "head": head, "base": base, "body": body, "draft": draft},
        )
        r.raise_for_status()
        return r.json()["html_url"]

    def rerun_failed_jobs(self, run_id):
        r = self._s.post(f"{API}/repos/{self.repo}/actions/runs/{run_id}/rerun-failed-jobs")
        r.raise_for_status()


# Matches the ISO timestamp GitHub prefixes onto every log line.
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z ?", re.MULTILINE)


def tail_logs(text, max_chars):
    """Strip timestamps and keep only the END of the log (where errors live)."""
    text = _TIMESTAMP.sub("", text)
    if len(text) <= max_chars:
        return text
    return "...[truncated]...\n" + text[-max_chars:]