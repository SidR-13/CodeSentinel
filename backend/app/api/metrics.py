from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.database import get_db
from app.models.review import Review
from app.models.user import User

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
async def get_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    result = await db.execute(
        select(
            func.count().label("total"),
            func.count(case((Review.status == "completed", 1))).label("completed"),
            func.count(case((Review.status == "failed", 1))).label("failed"),
            func.avg(
                case((
                    Review.status == "completed",
                    func.extract("epoch", Review.completed_at - Review.created_at) * 1000,
                ))
            ).label("avg_duration_ms"),
            func.count(case((Review.created_at >= since_24h, 1))).label("last_24h"),
        ).where(Review.user_id == current_user.id)
    )
    row = result.one()

    total = row.total or 0
    completed = row.completed or 0
    failed = row.failed or 0
    reviewed = completed + failed
    success_rate = round((completed / reviewed) * 100, 1) if reviewed > 0 else None

    return {
        "total_reviews": total,
        "avg_pipeline_duration_ms": round(float(row.avg_duration_ms), 0) if row.avg_duration_ms else None,
        "success_rate": success_rate,
        "reviews_last_24h": row.last_24h or 0,
    }
