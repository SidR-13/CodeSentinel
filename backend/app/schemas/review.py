from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class SubmitReviewRequest(BaseModel):
    pr_url: str


class IssueSchema(BaseModel):
    id: int
    category: str
    severity: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    description: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    affected_files: Optional[str] = None

    model_config = {"from_attributes": True}


class ReviewSummaryResponse(BaseModel):
    id: int
    pr_url: str
    repo_owner: str
    repo_name: str
    pr_number: int
    pr_title: Optional[str] = None
    overall_score: Optional[float] = None
    status: str
    total_issues: int
    critical_issues: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReviewDetailResponse(BaseModel):
    id: int
    pr_url: str
    repo_owner: str
    repo_name: str
    pr_number: int
    pr_title: Optional[str] = None
    overall_score: Optional[float] = None
    summary: Optional[str] = None
    status: str
    total_issues: int
    critical_issues: int
    positive_observations: Optional[List[str]] = None
    top_priorities: Optional[List[str]] = None
    error_message: Optional[str] = None
    issues: List[IssueSchema] = []
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    reviews: List[ReviewSummaryResponse]
    total: int


class PostCommentRequest(BaseModel):
    github_token: Optional[str] = None
