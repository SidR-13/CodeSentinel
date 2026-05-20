from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pr_url = Column(String(500), nullable=False, index=True)
    repo_owner = Column(String(100), nullable=False)
    repo_name = Column(String(100), nullable=False)
    pr_number = Column(Integer, nullable=False)
    pr_title = Column(String(500), nullable=True)
    overall_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending|processing|completed|failed
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    positive_observations = Column(JSON, nullable=True)
    top_priorities = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="reviews")
    issues = relationship("ReviewIssue", back_populates="review", cascade="all, delete-orphan", lazy="select")
    comments = relationship("ReviewComment", back_populates="review", cascade="all, delete-orphan", lazy="select")
