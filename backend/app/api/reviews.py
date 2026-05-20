import asyncio
import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.auth import get_current_user
from app.core.github_client import GitHubClient, parse_pr_url
from app.database import get_db
from app.models.review import Review
from app.models.review_issue import ReviewComment
from app.models.user import User
from app.schemas.review import (
    PostCommentRequest,
    ReviewDetailResponse,
    ReviewListResponse,
    ReviewSummaryResponse,
    SubmitReviewRequest,
)

settings = get_settings()
router = APIRouter(prefix="/api/reviews", tags=["reviews"])
logger = logging.getLogger(__name__)

QUEUE_KEY = "review_jobs"


def _redis_sync():
    import redis as _redis
    return _redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def _redis_async():
    return await aioredis.from_url(settings.REDIS_URL, decode_responses=True)


@router.post("", response_model=ReviewSummaryResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    payload: SubmitReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        owner, repo, pr_number = parse_pr_url(payload.pr_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check if same user already reviewed this exact PR URL
    existing = await db.execute(
        select(Review).where(
            Review.user_id == current_user.id,
            Review.pr_url == payload.pr_url,
            Review.status == "completed",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="You have already reviewed this PR. View it in your dashboard."
        )

    review = Review(
        user_id=current_user.id,
        pr_url=payload.pr_url,
        repo_owner=owner,
        repo_name=repo,
        pr_number=pr_number,
        status="pending",
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)
    await db.commit()  # commit before pushing to Redis so worker can find the row

    job = {
        "review_id": review.id,
        "pr_url": payload.pr_url,
        "owner": owner,
        "repo": repo,
        "pr_number": pr_number,
        "github_token": current_user.github_token,
    }
    r = _redis_sync()
    r.rpush(QUEUE_KEY, json.dumps(job))

    return ReviewSummaryResponse(
        id=review.id,
        pr_url=review.pr_url,
        repo_owner=review.repo_owner,
        repo_name=review.repo_name,
        pr_number=review.pr_number,
        pr_title=review.pr_title,
        overall_score=review.overall_score,
        status=review.status,
        total_issues=review.total_issues,
        critical_issues=review.critical_issues,
        created_at=review.created_at,
        completed_at=review.completed_at,
    )


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import case, cast, Float
    result = await db.execute(
        select(
            func.count().label("total"),
            func.count(case((Review.status == "completed", 1))).label("completed"),
            func.count(case((Review.status == "failed", 1))).label("failed"),
            func.count(case((Review.status == "pending", 1))).label("pending"),
            func.avg(case((Review.status == "completed", Review.overall_score))).label("avg_score"),
            func.sum(Review.total_issues).label("total_issues"),
            func.sum(Review.critical_issues).label("critical_issues"),
        ).where(Review.user_id == current_user.id)
    )
    row = result.one()
    return {
        "total": row.total or 0,
        "completed": row.completed or 0,
        "failed": row.failed or 0,
        "pending": row.pending or 0,
        "avg_score": round(float(row.avg_score), 1) if row.avg_score is not None else None,
        "total_issues": row.total_issues or 0,
        "critical_issues": row.critical_issues or 0,
    }


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    page: int = 1,
    per_page: int = 20,
    repo: str | None = None,
    status: str | None = None,
    score_min: float | None = None,
    score_max: float | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Review.user_id == current_user.id]
    if repo:
        filters.append(
            or_(
                Review.repo_name.ilike(f"%{repo}%"),
                Review.repo_owner.ilike(f"%{repo}%"),
                func.concat(Review.repo_owner, "/", Review.repo_name).ilike(f"%{repo}%"),
            )
        )
    if status:
        filters.append(Review.status == status)
    if score_min is not None:
        filters.append(Review.overall_score >= score_min)
    if score_max is not None:
        filters.append(Review.overall_score < score_max)

    offset = (page - 1) * per_page
    total_q = await db.execute(
        select(func.count()).select_from(Review).where(*filters)
    )
    total = total_q.scalar_one()

    result = await db.execute(
        select(Review)
        .where(*filters)
        .order_by(desc(Review.created_at))
        .offset(offset)
        .limit(per_page)
    )
    reviews = result.scalars().all()

    return ReviewListResponse(
        reviews=[ReviewSummaryResponse.model_validate(r) for r in reviews],
        total=total,
    )


@router.get("/{review_id}", response_model=ReviewDetailResponse)
async def get_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.issues))
        .where(Review.id == review_id, Review.user_id == current_user.id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    return ReviewDetailResponse.model_validate(review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.user_id == current_user.id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    await db.delete(review)


@router.get("/{review_id}/progress")
async def review_progress(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE endpoint — streams progress events from Redis pub/sub."""
    result = await db.execute(
        select(Review).where(Review.id == review_id, Review.user_id == current_user.id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")

    # If already done, emit a single terminal event immediately
    if review.status in ("completed", "failed"):
        async def immediate():
            event = json.dumps({"step": review.status, "message": review.status.capitalize(), "progress": 100, "status": review.status})
            yield f"data: {event}\n\n"
        return StreamingResponse(
            immediate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    async def stream():
        r = await _redis_async()
        pubsub = r.pubsub()
        channel = f"review:{review_id}:progress"
        await pubsub.subscribe(channel)
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = message["data"]
                yield f"data: {data}\n\n"
                try:
                    event = json.loads(data)
                    if event.get("status") in ("completed", "failed"):
                        break
                except json.JSONDecodeError:
                    pass
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{review_id}/post-comment", status_code=status.HTTP_201_CREATED)
async def post_github_comment(
    review_id: int,
    payload: PostCommentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.issues))
        .where(Review.id == review_id, Review.user_id == current_user.id)
    )
    review = result.scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != "completed":
        raise HTTPException(status_code=400, detail="Review is not yet completed")

    token = payload.github_token or current_user.github_token
    if not token:
        raise HTTPException(status_code=400, detail="GitHub token required to post comments")

    from app.core.review_pipeline import _build_github_comment
    body = _build_github_comment(
        {
            "summary": review.summary,
            "security_issues": [
                {"severity": i.severity, "file": i.file_path, "line": i.line_number, "description": i.description, "suggestion": i.suggestion}
                for i in review.issues if i.category == "security"
            ],
            "bugs": [
                {"severity": i.severity, "file": i.file_path, "line": i.line_number, "description": i.description, "suggestion": i.suggestion}
                for i in review.issues if i.category == "bug"
            ],
            "quality_issues": [
                {"severity": i.severity, "file": i.file_path, "line": i.line_number, "description": i.description, "suggestion": i.suggestion}
                for i in review.issues if i.category == "quality"
            ],
            "cross_file_issues": [
                {"affected_files": json.loads(i.affected_files or "[]"), "description": i.description, "suggestion": i.suggestion}
                for i in review.issues if i.category == "cross_file"
            ],
            "positive_observations": review.positive_observations or [],
            "top_priorities": review.top_priorities or [],
        },
        score=review.overall_score or 0,
        pr_url=review.pr_url,
    )

    github = GitHubClient(token=token)
    comment_data = await github.post_pr_comment(
        review.repo_owner, review.repo_name, review.pr_number, body, token
    )

    comment = ReviewComment(
        review_id=review.id,
        github_comment_id=comment_data.get("id"),
        posted_to_github=True,
        posted_at=datetime.now(timezone.utc),
        comment_body=body,
    )
    db.add(comment)

    return {"message": "Comment posted successfully", "github_comment_id": comment_data.get("id")}
