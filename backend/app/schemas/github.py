from pydantic import BaseModel
from typing import Optional


class ValidatePRRequest(BaseModel):
    pr_url: str


class ValidatePRResponse(BaseModel):
    valid: bool
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    pr_number: Optional[int] = None
    pr_title: Optional[str] = None
    pr_state: Optional[str] = None
    changed_files: Optional[int] = None
    error: Optional[str] = None
