"""Initial schema: users, resumes, job descriptions, analyses, skills, matches,
evidence, roadmaps, tasks, progress history and feedback.

The baseline migration creates the tables from the SQLAlchemy models so that the
schema and the models can never drift apart. Later schema changes should be
added as new revisions with:  alembic revision --autogenerate -m "describe change"

Revision ID: 0001
Revises:
Create Date: 2026-11-01
"""

from alembic import op

import app.models  # noqa: F401
from app.database.session import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
