"""Add admin user

Revision ID: 0002
Revises: 0001
Create Date: 2023-05-22 00:01:00.000000

"""
import os
import sys
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.sql import text

from alembic import op

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import the password hashing function

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get database connection
    connection = op.get_bind()

    # Get admin credentials from environment variables
    admin_email = os.getenv("FIRST_SUPERUSER", "admin@example.com")
    admin_password = os.getenv("FIRST_SUPERUSER_PASSWORD", "admin")

    if not admin_email or not admin_password:
        print(
            "Warning: FIRST_SUPERUSER or FIRST_SUPERUSER_PASSWORD not set in environment"  # noqa: E501
        )
        return

    # Import here to avoid circular imports
    from app.core.security import get_password_hash

    # Check if admin user already exists
    result = connection.execute(
        text("SELECT id FROM users WHERE email = :email"), {"email": admin_email}
    ).fetchone()

    if not result:
        # Create admin user
        hashed_password = get_password_hash(admin_password)
        now = datetime.utcnow()

        # Using SQLAlchemy Core to insert the admin user
        op.bulk_insert(
            sa.table(
                "users",
                sa.column("email", sa.String),
                sa.column("hashed_password", sa.String),
                sa.column("full_name", sa.String),
                sa.column("is_active", sa.Boolean),
                sa.column("is_superuser", sa.Boolean),
                sa.column("created_at", sa.DateTime),
                sa.column("updated_at", sa.DateTime),
            ),
            [
                {
                    "email": admin_email,
                    "hashed_password": hashed_password,
                    "full_name": "Admin User",
                    "is_active": True,
                    "is_superuser": True,
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )
        print(f"Created admin user: {admin_email}")
    else:
        print(f"Admin user {admin_email} already exists, skipping creation")


def downgrade() -> None:
    # Get admin email from environment variables
    admin_email = os.getenv("FIRST_SUPERUSER", "admin@example.com")

    # Get database connection
    connection = op.get_bind()

    # Remove admin user using parameterized query
    connection.execute(
        text("DELETE FROM users WHERE email = :email"), {"email": admin_email}
    )
    print(f"Removed admin user: {admin_email}")

    # Note: We don't drop the users table here as it might contain other data
    # op.execute("""
    #     SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));
    # """)  # noqa: E501
