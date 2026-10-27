"""persist SENAFÓNICA module progress

Revision ID: c9f53a1bd620
Revises: a4c81f26e7b3
"""
from alembic import op
import sqlalchemy as sa


revision = "c9f53a1bd620"
down_revision = "a4c81f26e7b3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("progress", sa.Column("module_progress_json", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("progress", "module_progress_json")
