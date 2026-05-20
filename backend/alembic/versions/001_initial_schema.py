"""Initial schema — users, reviews, review_issues, review_comments

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("github_username", sa.String(100), nullable=True),
        sa.Column("github_token", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pr_url", sa.String(500), nullable=False, index=True),
        sa.Column("repo_owner", sa.String(100), nullable=False),
        sa.Column("repo_name", sa.String(100), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("pr_title", sa.String(500), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total_issues", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_issues", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("positive_observations", sa.JSON(), nullable=True),
        sa.Column("top_priorities", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "review_issues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "review_id",
            sa.Integer(),
            sa.ForeignKey("reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("suggestion", sa.Text(), nullable=True),
        sa.Column("code_snippet", sa.Text(), nullable=True),
        sa.Column("affected_files", sa.Text(), nullable=True),
    )

    op.create_table(
        "review_comments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "review_id",
            sa.Integer(),
            sa.ForeignKey("reviews.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("github_comment_id", sa.Integer(), nullable=True),
        sa.Column("posted_to_github", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("comment_body", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("review_comments")
    op.drop_table("review_issues")
    op.drop_table("reviews")
    op.drop_table("users")
