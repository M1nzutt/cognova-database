"""Subjects with a concurrency-safe five-active-subject limit per user."""

import sqlalchemy as sa
from alembic import op

revision = "0004_subjects"
down_revision = "0003_onboarding_questionnaire"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.Text(), nullable=False),
        sa.Column("color_base", sa.Text(), nullable=False),
        sa.Column("color_shade", sa.SmallInteger(), nullable=False),
        sa.Column("active_slot", sa.SmallInteger(), nullable=True),
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
            name="fk_subjects_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "char_length(name) BETWEEN 1 AND 20 AND name = btrim(name) "
            "AND name !~ '^[[:space:]]*$'",
            name="ck_subjects_name",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_subjects_status",
        ),
        sa.CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="ck_subjects_difficulty",
        ),
        sa.CheckConstraint(
            "color_base ~ '^[a-z][a-z0-9_-]{0,31}$'",
            name="ck_subjects_color_base",
        ),
        sa.CheckConstraint(
            "color_shade BETWEEN 0 AND 1000",
            name="ck_subjects_color_shade",
        ),
        sa.CheckConstraint(
            "(status = 'active' AND active_slot IS NOT NULL "
            "AND active_slot BETWEEN 1 AND 5) "
            "OR (status = 'archived' AND active_slot IS NULL)",
            name="ck_subjects_active_slot",
        ),
        sa.UniqueConstraint("user_id", "active_slot", name="uq_subjects_active_slot"),
    )
    op.create_index(
        "uq_subjects_user_name_lower",
        "subjects",
        ["user_id", sa.text("lower(name)")],
        unique=True,
    )
    op.create_index("ix_subjects_user_status", "subjects", ["user_id", "status"])


def downgrade() -> None:
    # Include archived rows: they remain valuable data, not disposable capacity.
    op.execute("LOCK TABLE subjects IN ACCESS EXCLUSIVE MODE")
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM subjects) THEN
                RAISE EXCEPTION 'Downgrade blocked: subjects exist';
            END IF;
        END $$
    """)
    # No CASCADE: any future dependent objects also prevent destructive rollback.
    op.drop_table("subjects")
