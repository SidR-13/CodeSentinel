from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ReviewIssue(Base):
    __tablename__ = "review_issues"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)   # security|bug|quality|cross_file
    severity = Column(String(20), nullable=False)   # CRITICAL|HIGH|MEDIUM|LOW
    file_path = Column(String(500), nullable=True)
    line_number = Column(Integer, nullable=True)
    description = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)
    code_snippet = Column(Text, nullable=True)
    affected_files = Column(Text, nullable=True)    # JSON-encoded list for cross_file issues

    review = relationship("Review", back_populates="issues")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    github_comment_id = Column(Integer, nullable=True)
    posted_to_github = Column(Boolean, default=False)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    comment_body = Column(Text, nullable=False)

    review = relationship("Review", back_populates="comments")
