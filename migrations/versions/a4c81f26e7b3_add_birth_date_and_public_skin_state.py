"""add birth date and public skin state

Revision ID: a4c81f26e7b3
Revises: edd7b909160e
"""
from alembic import op
import sqlalchemy as sa


revision = "a4c81f26e7b3"
down_revision = "edd7b909160e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column(
        "user_gamification",
        sa.Column(
            "equipped_skin",
            sa.String(length=80),
            nullable=False,
            server_default="skin_tiple_noble",
        ),
    )
    op.add_column(
        "user_gamification",
        sa.Column(
            "unlocked_skins_json",
            sa.Text(),
            nullable=False,
            server_default='["skin_tiple_noble"]',
        ),
    )


def downgrade():
    op.drop_column("user_gamification", "unlocked_skins_json")
    op.drop_column("user_gamification", "equipped_skin")
    op.drop_column("users", "birth_date")
