"""add project creator email

Revision ID: f1b7d2f2d9f1
Revises: c153f8c4e111
Create Date: 2026-04-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1b7d2f2d9f1'
down_revision = 'c153f8c4e111'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('created_by_email', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('projects', 'created_by_email')
