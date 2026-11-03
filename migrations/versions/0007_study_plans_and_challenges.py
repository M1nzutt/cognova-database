"""Persist study plans, resource links, decisions and contextual challenges."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_study_plans_and_challenges"
down_revision = "0006_study_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    _study_plans()
    _plan_relationships()
    _plan_decisions()


def downgrade() -> None:
    op.execute(
        "LOCK TABLE users, subjects, activities, study_sessions, study_plans, "
        "study_plan_subjects, study_plan_activities, study_plan_sessions, "
        "study_plan_decisions "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM study_plans)
               OR EXISTS (SELECT 1 FROM study_plan_subjects)
               OR EXISTS (SELECT 1 FROM study_plan_activities)
               OR EXISTS (SELECT 1 FROM study_plan_sessions)
               OR EXISTS (SELECT 1 FROM study_plan_decisions) THEN
                RAISE EXCEPTION 'Downgrade blocked: study plan data exists';
            END IF;
        END $$
    """)
    op.drop_table("study_plan_decisions")
    op.drop_table("study_plan_sessions")
    op.drop_table("study_plan_activities")
    op.drop_table("study_plan_subjects")
    op.drop_table("study_plans")
    op.drop_constraint(
        "uq_study_sessions_user_subject_activity_id",
        "study_sessions",
        type_="unique",
    )
    op.drop_constraint(
        "uq_study_sessions_user_subject_id", "study_sessions", type_="unique"
    )


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


def _plan_relationships() -> None:
    op.create_unique_constraint(
        "uq_study_sessions_user_subject_id",
        "study_sessions",
        ["user_id", "subject_id", "id"],
    )

    op.create_unique_constraint(
        "uq_study_sessions_user_subject_activity_id",
        "study_sessions",
        ["user_id", "subject_id", "activity_id", "id"],
    )
    op.create_table(
        "study_plan_subjects",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id", "plan_id"],
            ["study_plans.user_id", "study_plans.id"],
            name="fk_study_plan_subjects_plan",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "subject_id"],
            ["subjects.user_id", "subjects.id"],
            name="fk_study_plan_subjects_owner_subject",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "plan_id", "subject_id", name="pk_study_plan_subjects"
        ),
    )
    op.create_table(
        "study_plan_activities",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id", "plan_id", "subject_id"],
            [
                "study_plan_subjects.user_id",
                "study_plan_subjects.plan_id",
                "study_plan_subjects.subject_id",
            ],
            name="fk_study_plan_activities_plan_subject",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "subject_id", "activity_id"],
            ["activities.user_id", "activities.subject_id", "activities.id"],
            name="fk_study_plan_activities_owner_subject_activity",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "plan_id", "activity_id", name="pk_study_plan_activities"
        ),
        sa.UniqueConstraint(
            "user_id",
            "plan_id",
            "subject_id",
            "activity_id",
            name="uq_study_plan_activities_owner_context",
        ),
    )
    op.create_table(
        "study_plan_sessions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("study_session_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id", "plan_id", "subject_id"],
            [
                "study_plan_subjects.user_id",
                "study_plan_subjects.plan_id",
                "study_plan_subjects.subject_id",
            ],
            name="fk_study_plan_sessions_plan_subject",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "subject_id", "study_session_id"],
            [
                "study_sessions.user_id",
                "study_sessions.subject_id",
                "study_sessions.id",
            ],
            name="fk_study_plan_sessions_owner_subject_session",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "plan_id", "study_session_id", name="pk_study_plan_sessions"
        ),
        sa.UniqueConstraint(
            "user_id",
            "plan_id",
            "subject_id",
            "study_session_id",
            name="uq_study_plan_sessions_owner_context",
        ),
    )


def _plan_decisions() -> None:
    op.create_table(
        "study_plan_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("field_path", sa.Text(), nullable=True),
        sa.Column("proposed_value", postgresql.JSONB(), nullable=True),
        sa.Column("chosen_value", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "plan_id"],
            ["study_plans.user_id", "study_plans.id"],
            name="fk_study_plan_decisions_plan",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            "action IN ('accepted','edited','rejected','regenerated')",
            name="ck_study_plan_decisions_action",
        ),
        sa.CheckConstraint(
            "field_path IS NULL OR (char_length(field_path) BETWEEN 1 AND 200 "
            "AND field_path = btrim(field_path) "
            "AND field_path !~ '^[[:space:]]*$')",
            name="ck_study_plan_decisions_field_path",
        ),
        sa.CheckConstraint(
            "(proposed_value IS NULL OR "
            "octet_length(proposed_value::text) <= 65536) AND "
            "(chosen_value IS NULL OR octet_length(chosen_value::text) <= 65536)",
            name="ck_study_plan_decisions_value_size",
        ),
        sa.CheckConstraint(
            "(action = 'accepted' AND proposed_value IS NOT NULL "
            "AND chosen_value IS NOT NULL) OR "
            "(action = 'edited' AND field_path IS NOT NULL "
            "AND proposed_value IS NOT NULL AND chosen_value IS NOT NULL "
            "AND proposed_value IS DISTINCT FROM chosen_value) OR "
            "(action IN ('rejected','regenerated') "
            "AND proposed_value IS NOT NULL AND chosen_value IS NULL)",
            name="ck_study_plan_decisions_values",
        ),
        sa.CheckConstraint("isfinite(created_at)", name="ck_study_plan_decisions_time"),
    )
