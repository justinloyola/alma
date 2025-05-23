"""Initial migration

Revision ID: 0001
Revises:
Create Date: 2023-05-22 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.sql import func

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column(
            "email", sa.String(length=255), nullable=False, comment="User email address"
        ),
        sa.Column(
            "hashed_password",
            sa.String(length=255),
            nullable=False,
            comment="Hashed password",
        ),
        sa.Column(
            "full_name", sa.String(length=255), nullable=True, comment="User full name"
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
            comment="Is user active?",
        ),
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Is user a superuser?",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=func.now(),
            nullable=False,
            comment="Creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            onupdate=func.now(),
            comment="Last update timestamp",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Create leads table
    op.create_table(
        "leads",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column(
            "first_name", sa.String(length=100), nullable=False, comment="First name"
        ),
        sa.Column(
            "last_name", sa.String(length=100), nullable=False, comment="Last name"
        ),
        sa.Column(
            "email", sa.String(length=255), nullable=False, comment="Email address"
        ),
        sa.Column(
            "resume_storage_type",
            sa.String(20),
            server_default="filesystem",
            nullable=False,
            comment="Storage type for resume (filesystem, postgres)",
        ),
        sa.Column(
            "resume_path",
            sa.String(length=512),
            nullable=True,
            comment="Path to resume file",
        ),
        sa.Column(
            "resume_original_filename",
            sa.String(length=255),
            nullable=True,
            comment="Original filename of resume",
        ),
        sa.Column(
            "resume_mime_type",
            sa.String(length=100),
            nullable=True,
            comment="MIME type of resume",
        ),
        sa.Column(
            "resume_size",
            sa.Integer(),
            nullable=True,
            comment="Size of resume in bytes",
        ),
        sa.Column(
            "resume_metadata",
            sa.JSON(),
            nullable=True,
            comment="Additional metadata for resume",
        ),
        sa.Column(
            "status",
            sa.String(20),
            server_default="pending",
            nullable=False,
            comment="Lead status (pending, reached_out)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=func.now(),
            nullable=False,
            comment="Creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            onupdate=func.now(),
            comment="Last update timestamp",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Create indexes
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_leads_email"), "leads", ["email"], unique=True)

    # Note: Check constraints are handled at the application level for SQLite compatibility
    # as SQLite has limited ALTER TABLE support


def downgrade() -> None:
    """Downgrade database schema by one revision."""
    # Drop indexes
    op.drop_index(op.f("ix_leads_email"), table_name="leads")
    op.drop_index(op.f("ix_users_email"), table_name="users")

    # Drop tables
    op.drop_table("leads")
    op.drop_table("users")
