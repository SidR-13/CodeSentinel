"""
Review worker — run as a separate process alongside the FastAPI server.
Pulls jobs from the Redis list 'review_jobs' (BLPOP) and runs ReviewPipeline.

Usage:
    python -m app.worker.review_worker
"""
import asyncio
import json
import logging
import signal
import sys

import redis

from app.config import get_settings
from app.core.review_pipeline import ReviewPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")
settings = get_settings()

QUEUE_KEY = "review_jobs"
SHUTDOWN = asyncio.Event()


def _handle_signal(sig, frame):
    logger.info("Received signal %s — shutting down worker", sig)
    SHUTDOWN.set()


async def process_job(job: dict):
    review_id = job["review_id"]
    pr_url = job["pr_url"]
    owner = job["owner"]
    repo = job["repo"]
    pr_number = job["pr_number"]
    github_token = job.get("github_token")

    logger.info("Processing review %d for %s", review_id, pr_url)
    pipeline = ReviewPipeline(review_id=review_id, github_token=github_token)
    await pipeline.run(pr_url=pr_url, owner=owner, repo=repo, pr_number=pr_number)
    logger.info("Review %d completed", review_id)


async def main():
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    r = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    logger.info("Worker started — waiting for jobs on '%s'", QUEUE_KEY)

    while not SHUTDOWN.is_set():
        # BLPOP blocks for up to 2 seconds, then loops so we can check SHUTDOWN
        item = r.blpop(QUEUE_KEY, timeout=2)
        if item is None:
            continue

        _, raw = item
        try:
            job = json.loads(raw)
            await process_job(job)
        except Exception:
            logger.exception("Unhandled error processing job: %s", raw)

    logger.info("Worker shut down cleanly")


if __name__ == "__main__":
    asyncio.run(main())
