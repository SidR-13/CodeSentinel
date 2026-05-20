import json
import logging
import anthropic
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Static instruction — cached by Anthropic after first call
SYSTEM_PROMPT = """You are a senior software engineer performing a thorough code review. \
Analyze the pull request diff provided by the user and return a structured JSON review.

Return ONLY valid JSON — no markdown, no explanation, just the JSON object — matching this exact structure:
{
  "summary": "2-3 sentence summary of the overall change and its quality",
  "security_issues": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "file": "path/to/file.py",
      "line": 42,
      "description": "Clear description of the security issue",
      "suggestion": "Specific fix suggestion"
    }
  ],
  "bugs": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "file": "path/to/file.py",
      "line": 15,
      "description": "Description of the bug",
      "suggestion": "How to fix it"
    }
  ],
  "quality_issues": [
    {
      "severity": "HIGH|MEDIUM|LOW",
      "file": "path/to/file.py",
      "line": 8,
      "description": "Code quality problem",
      "suggestion": "Improvement suggestion"
    }
  ],
  "cross_file_issues": [
    {
      "severity": "HIGH|MEDIUM|LOW",
      "affected_files": ["file1.py", "file2.py"],
      "description": "Issue spanning multiple files",
      "suggestion": "How to resolve it"
    }
  ],
  "positive_observations": [
    "Something done well"
  ],
  "top_priorities": [
    "Most important thing to fix before merging"
  ]
}

Be specific with file paths and line numbers. Focus on real issues, not style nitpicks."""

# PR-specific context template — not cached (changes per review)
USER_PROMPT_TEMPLATE = """PR Title: {title}
Repository: {owner}/{repo}
Files changed: {file_list}

Dependency relationships detected:
{dependency_graph}

Diff (truncated to {token_count} tokens):
{diff}"""

MOCK_REVIEW = {
    "summary": "This PR introduces a user authentication module with JWT token handling and password management. The implementation shows good structure but has critical security vulnerabilities in the SQL query construction and missing token expiration validation that must be fixed before merging.",
    "security_issues": [
        {
            "severity": "CRITICAL",
            "file": "auth/handlers.py",
            "line": 45,
            "description": "SQL query constructed via string concatenation — vulnerable to SQL injection. User-controlled input flows directly into the query string.",
            "suggestion": "Use parameterized queries: `cursor.execute('SELECT * FROM users WHERE email = %s', (email,))` or switch to an ORM.",
        },
        {
            "severity": "HIGH",
            "file": "auth/tokens.py",
            "line": 23,
            "description": "JWT tokens are decoded without verifying the expiration claim. Expired tokens remain valid indefinitely.",
            "suggestion": "Pass `options={'verify_exp': True}` to `jwt.decode()` and catch `ExpiredSignatureError`.",
        },
    ],
    "bugs": [
        {
            "severity": "HIGH",
            "file": "auth/handlers.py",
            "line": 67,
            "description": "Race condition in token refresh — multiple concurrent requests can each pass the expiry check and generate duplicate tokens before any are stored.",
            "suggestion": "Use a distributed lock (Redis SETNX) around the token refresh section.",
        },
        {
            "severity": "MEDIUM",
            "file": "auth/middleware.py",
            "line": 34,
            "description": "Exception caught but swallowed with bare `except: pass` — authentication failures silently succeed.",
            "suggestion": "Replace with `except AuthenticationError: return 401` and log the error.",
        },
    ],
    "quality_issues": [
        {
            "severity": "MEDIUM",
            "file": "auth/tokens.py",
            "line": 12,
            "description": "Magic string `'HS256'` used directly instead of a named constant.",
            "suggestion": "Define `ALGORITHM = 'HS256'` as a module-level constant and reference it everywhere.",
        },
        {
            "severity": "LOW",
            "file": "auth/handlers.py",
            "line": 89,
            "description": "Function `validate_and_login` does three unrelated things — validation, DB lookup, and session creation.",
            "suggestion": "Split into `validate_credentials()`, `find_user()`, and `create_session()` for testability.",
        },
    ],
    "cross_file_issues": [
        {
            "severity": "MEDIUM",
            "affected_files": ["auth/handlers.py", "auth/tokens.py", "auth/middleware.py"],
            "description": "Inconsistent error handling — handlers.py raises exceptions, tokens.py returns None on failure, middleware.py swallows errors. Callers cannot rely on a consistent contract.",
            "suggestion": "Define a custom `AuthenticationError` exception hierarchy and raise it consistently across all three modules.",
        }
    ],
    "positive_observations": [
        "Correct use of bcrypt for password hashing with appropriate cost factor (12)",
        "Token expiration time is configurable via environment variables — good 12-factor app practice",
        "Unit tests exist for the token generation module with good coverage of the happy path",
    ],
    "top_priorities": [
        "Fix SQL injection in auth/handlers.py:45 — this is an immediate critical vulnerability",
        "Add JWT expiration validation in auth/tokens.py:23 — expired tokens are currently accepted forever",
        "Resolve the race condition in token refresh (auth/handlers.py:67) before any load testing",
    ],
}


def _parse_json_response(raw: str) -> dict:
    """Strip markdown fences if present, then parse JSON."""
    text = raw.strip()
    if text.startswith("```"):
        parts = text.split("```")
        # parts[1] is the content between the first pair of fences
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


class ClaudeClient:
    def __init__(self):
        self._mock = settings.AI_MOCK
        if not self._mock:
            self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def review_pr(
        self,
        diff: str,
        pr_title: str,
        owner: str,
        repo: str,
        file_list: list[str],
        dependency_graph: str,
        token_count: int,
    ) -> dict:
        if self._mock:
            return MOCK_REVIEW

        user_content = USER_PROMPT_TEMPLATE.format(
            title=pr_title,
            owner=owner,
            repo=repo,
            file_list=", ".join(file_list),
            dependency_graph=dependency_graph or "No dependency relationships detected",
            diff=diff,
            token_count=token_count,
        )

        for attempt in range(2):
            try:
                message = await self._client.messages.create(
                    model=settings.CLAUDE_MODEL,
                    max_tokens=4096,
                    system=[
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=[{"role": "user", "content": user_content}],
                    extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
                )
                raw = message.content[0].text
                result = _parse_json_response(raw)
                logger.info(
                    "Claude usage — input: %d, output: %d, cache_read: %d, cache_write: %d",
                    message.usage.input_tokens,
                    message.usage.output_tokens,
                    getattr(message.usage, "cache_read_input_tokens", 0),
                    getattr(message.usage, "cache_creation_input_tokens", 0),
                )
                return result
            except json.JSONDecodeError as exc:
                if attempt == 0:
                    logger.warning("Claude returned malformed JSON, retrying (attempt 1): %s", exc)
                    continue
                raise ValueError(f"Claude returned invalid JSON after 2 attempts: {exc}") from exc
