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
        sa.Column("bandola_correct_streak", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_gamification",
        sa.Column(
            "tonic_scales_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "user_gamification",
        sa.Column("daily_streak", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_gamification",
        sa.Column("last_daily_challenge", sa.Date(), nullable=True),
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
    op.drop_column("user_gamification", "last_daily_challenge")
    op.drop_column("user_gamification", "daily_streak")
    op.drop_column("user_gamification", "tonic_scales_json")
    op.drop_column("user_gamification", "bandola_correct_streak")
    op.drop_column("user_gamification", "unlocked_skins_json")
    op.drop_column("user_gamification", "equipped_skin")
    op.drop_column("users", "birth_date")
