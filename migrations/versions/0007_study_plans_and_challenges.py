"""Persist study plans, resource links, decisions and contextual challenges."""

import sqlalchemy as sa
from alembic import op

revision = "0007_study_plans_and_challenges"
down_revision = "0006_study_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _study_plans()


def downgrade() -> None:
    op.execute("LOCK TABLE users, study_plans IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM study_plans) THEN
                RAISE EXCEPTION 'Downgrade blocked: study plans exist';
            END IF;
        END $$
    """)
    op.drop_table("study_plans")


def _study_plans() -> None:
    op.create_table(
        "study_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_study_plans_user",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.UniqueConstraint("user_id", "id", name="uq_study_plans_user_id_id"),
        sa.CheckConstraint(
            "char_length(name) BETWEEN 1 AND 100 AND name = btrim(name) "
            "AND name !~ '^[[:space:]]*$'",
            name="ck_study_plans_name",
        ),
        sa.CheckConstraint(
            "char_length(objective) BETWEEN 1 AND 2000 "
            "AND objective = btrim(objective) "
            "AND objective !~ '^[[:space:]]*$'",
            name="ck_study_plans_objective",
        ),
        sa.CheckConstraint(
            "isfinite(start_at) AND isfinite(end_at) AND end_at > start_at",
            name="ck_study_plans_dates",
        ),
        sa.CheckConstraint(
            "status IN ('draft','active','completed','abandoned')",
            name="ck_study_plans_status",
        ),
        sa.CheckConstraint("source IN ('ai','manual')", name="ck_study_plans_source"),
        sa.CheckConstraint(
            "isfinite(created_at) AND isfinite(updated_at) "
            "AND updated_at >= created_at",
            name="ck_study_plans_timestamps",
        ),
    )
