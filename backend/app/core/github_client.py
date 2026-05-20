import re
import httpx
from typing import Optional, Tuple
from app.config import get_settings

settings = get_settings()

PR_URL_PATTERN = re.compile(
    r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
)


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    """Returns (owner, repo, pr_number) or raises ValueError."""
    m = PR_URL_PATTERN.match(url.strip().rstrip("/"))
    if not m:
        raise ValueError(f"Not a valid GitHub PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self._token = token or settings.GITHUB_TOKEN
        self._base = settings.GITHUB_API_URL

    def _headers(self, accept: str = "application/vnd.github+json") -> dict:
        h = {"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    async def get_pr_info(self, owner: str, repo: str, pr_number: int) -> dict:
        url = f"{self._base}/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._headers())
            if resp.status_code == 404:
                raise ValueError(f"PR not found: {owner}/{repo}#{pr_number}")
            if resp.status_code == 403:
                raise ValueError("GitHub rate limit exceeded or access denied")
            resp.raise_for_status()
            return resp.json()

    async def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        url = f"{self._base}/repos/{owner}/{repo}/pulls/{pr_number}"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(
                url,
                headers=self._headers(accept="application/vnd.github.v3.diff"),
                follow_redirects=True,
            )
            resp.raise_for_status()
            return resp.text

    async def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list:
        url = f"{self._base}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._headers(), params={"per_page": 100})
            resp.raise_for_status()
            return resp.json()

    async def post_pr_comment(
        self, owner: str, repo: str, pr_number: int, body: str, token: str
    ) -> dict:
        url = f"{self._base}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        headers = self._headers()
        headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, headers=headers, json={"body": body})
            resp.raise_for_status()
            return resp.json()
