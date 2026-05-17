"""fix_meeting_date_timezone

Revision ID: 769e4d56459c
Revises: 2efde82c040b
Create Date: 2026-05-13 00:46:24.630976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '769e4d56459c'
down_revision: Union[str, None] = '2efde82c040b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.alter_column(
        "meetings",
        "meeting_date",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        postgresql_using="meeting_date AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "meetings",
        "meeting_date",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
    )


