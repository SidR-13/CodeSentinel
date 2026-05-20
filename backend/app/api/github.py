from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.auth import get_current_user
from app.core.github_client import GitHubClient, parse_pr_url
from app.schemas.github import ValidatePRRequest, ValidatePRResponse

router = APIRouter(prefix="/api/github", tags=["github"])


@router.post("/validate", response_model=ValidatePRResponse)
async def validate_pr(payload: ValidatePRRequest, current_user: User = Depends(get_current_user)):
    try:
        owner, repo, pr_number = parse_pr_url(payload.pr_url)
    except ValueError as e:
        return ValidatePRResponse(valid=False, error=str(e))

    client = GitHubClient(token=current_user.github_token)
    try:
        pr_info = await client.get_pr_info(owner, repo, pr_number)
        return ValidatePRResponse(
            valid=True,
            repo_owner=owner,
            repo_name=repo,
            pr_number=pr_number,
            pr_title=pr_info.get("title"),
            pr_state=pr_info.get("state"),
            changed_files=pr_info.get("changed_files"),
        )
    except ValueError as e:
        return ValidatePRResponse(valid=False, error=str(e))
    except Exception as e:
        return ValidatePRResponse(valid=False, error=f"GitHub API error: {e}")
