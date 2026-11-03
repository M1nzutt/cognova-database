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
    _study_challenges()
    _indexes()


def downgrade() -> None:
    op.execute(
        "LOCK TABLE users, subjects, activities, study_sessions, study_plans, "
        "study_plan_subjects, study_plan_activities, study_plan_sessions, "
        "study_plan_decisions, study_challenges "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM study_plans)
               OR EXISTS (SELECT 1 FROM study_plan_subjects)
               OR EXISTS (SELECT 1 FROM study_plan_activities)
               OR EXISTS (SELECT 1 FROM study_plan_sessions)
               OR EXISTS (SELECT 1 FROM study_plan_decisions)
               OR EXISTS (SELECT 1 FROM study_challenges) THEN
                RAISE EXCEPTION 'Downgrade blocked: study plan data exists';
            END IF;
        END $$
    """)
    op.drop_table("study_challenges")
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


def _study_challenges() -> None:
    op.create_table(
        "study_challenges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=True),
        sa.Column("activity_id", sa.Integer(), nullable=True),
        sa.Column("study_session_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_value", postgresql.JSONB(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("generation_criteria", postgresql.JSONB(), nullable=False),
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
            ["user_id", "plan_id"],
            ["study_plans.user_id", "study_plans.id"],
            name="fk_study_challenges_plan",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "plan_id", "subject_id"],
            [
                "study_plan_subjects.user_id",
                "study_plan_subjects.plan_id",
                "study_plan_subjects.subject_id",
            ],
            name="fk_study_challenges_plan_subject",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "plan_id", "subject_id", "activity_id"],
            [
                "study_plan_activities.user_id",
                "study_plan_activities.plan_id",
                "study_plan_activities.subject_id",
                "study_plan_activities.activity_id",
            ],
            name="fk_study_challenges_plan_activity",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "plan_id", "subject_id", "study_session_id"],
            [
                "study_plan_sessions.user_id",
                "study_plan_sessions.plan_id",
                "study_plan_sessions.subject_id",
                "study_plan_sessions.study_session_id",
            ],
            name="fk_study_challenges_plan_session",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "subject_id", "activity_id", "study_session_id"],
            [
                "study_sessions.user_id",
                "study_sessions.subject_id",
                "study_sessions.activity_id",
                "study_sessions.id",
            ],
            name="fk_study_challenges_session_activity_consistency",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            "char_length(title) BETWEEN 1 AND 100 AND title = btrim(title) "
            "AND title !~ '^[[:space:]]*$'",
            name="ck_study_challenges_title",
        ),
        sa.CheckConstraint(
            "char_length(description) BETWEEN 1 AND 2000 "
            "AND description = btrim(description) "
            "AND description !~ '^[[:space:]]*$'",
            name="ck_study_challenges_description",
        ),
        sa.CheckConstraint(
            "target_type IN ('study_minutes','activity_completion',"
            "'session_completion','subject_mastery','custom')",
            name="ck_study_challenges_target_type",
        ),
        sa.CheckConstraint(
            "CASE WHEN jsonb_typeof(target_value) <> 'object' "
            "OR octet_length(target_value::text) NOT BETWEEN 2 AND 4096 "
            "THEN false "
            "WHEN target_type = 'study_minutes' THEN "
            "(subject_id IS NOT NULL OR study_session_id IS NOT NULL) "
            "AND target_value ? 'minutes' "
            "AND target_value - 'minutes' = '{}'::jsonb "
            "AND jsonb_typeof(target_value->'minutes') = 'number' "
            "AND CASE WHEN target_value->>'minutes' ~ '^[1-9][0-9]{0,3}$' "
            "THEN (target_value->>'minutes')::integer BETWEEN 1 AND 1440 "
            "ELSE false END "
            "WHEN target_type = 'activity_completion' THEN "
            "activity_id IS NOT NULL "
            'AND target_value = \'{"status":"completed"}\'::jsonb '
            "WHEN target_type = 'session_completion' THEN "
            "study_session_id IS NOT NULL "
            'AND target_value = \'{"lifecycle":"finished"}\'::jsonb '
            "WHEN target_type = 'subject_mastery' THEN "
            "subject_id IS NOT NULL "
            "AND target_value ?& ARRAY['criterion','threshold'] "
            "AND target_value - 'criterion' - 'threshold' = '{}'::jsonb "
            "AND jsonb_typeof(target_value->'criterion') = 'string' "
            "AND char_length(btrim(target_value->>'criterion')) BETWEEN 1 AND 200 "
            "AND CASE WHEN jsonb_typeof(target_value->'threshold') = 'number' "
            "AND target_value->>'threshold' ~ '^(100|[1-9]?[0-9])$' "
            "THEN (target_value->>'threshold')::integer BETWEEN 1 AND 100 "
            "ELSE false END "
            "WHEN target_type = 'custom' THEN target_value <> '{}'::jsonb "
            "ELSE false END",
            name="ck_study_challenges_target_value",
        ),
        sa.CheckConstraint(
            "(subject_id IS NOT NULL) OR "
            "(activity_id IS NULL AND study_session_id IS NULL)",
            name="ck_study_challenges_resource_subject",
        ),
        sa.CheckConstraint(
            "(start_at IS NULL OR isfinite(start_at)) AND "
            "(deadline IS NULL OR isfinite(deadline)) AND "
            "(start_at IS NULL OR deadline IS NULL OR deadline >= start_at)",
            name="ck_study_challenges_dates",
        ),
        sa.CheckConstraint(
            "status IN ('pending','in_progress','completed','failed','cancelled')",
            name="ck_study_challenges_status",
        ),
        sa.CheckConstraint(
            "source IN ('ai','manual')", name="ck_study_challenges_source"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(generation_criteria) = 'object' "
            "AND generation_criteria <> '{}'::jsonb "
            "AND octet_length(generation_criteria::text) <= 16384",
            name="ck_study_challenges_generation_criteria",
        ),
        sa.CheckConstraint(
            "isfinite(created_at) AND isfinite(updated_at) "
            "AND updated_at >= created_at",
            name="ck_study_challenges_timestamps",
        ),
    )


def _indexes() -> None:
    op.create_index(
        "ix_study_plans_user_status_start",
        "study_plans",
        ["user_id", "status", "start_at", "id"],
    )
    op.create_index(
        "ix_study_plans_user_end", "study_plans", ["user_id", "end_at", "id"]
    )
    op.create_index(
        "ix_study_plan_subjects_user_subject_plan",
        "study_plan_subjects",
        ["user_id", "subject_id", "plan_id"],
    )
    op.create_index(
        "ix_study_plan_activities_user_subject_activity",
        "study_plan_activities",
        ["user_id", "subject_id", "activity_id"],
    )
    op.create_index(
        "ix_study_plan_sessions_user_subject_session",
        "study_plan_sessions",
        ["user_id", "subject_id", "study_session_id"],
    )
    op.create_index(
        "ix_study_plan_decisions_user_plan_created",
        "study_plan_decisions",
        ["user_id", "plan_id", "created_at", "id"],
    )
    op.create_index(
        "ix_study_challenges_user_status_deadline",
        "study_challenges",
        ["user_id", "status", "deadline", "id"],
    )
    op.create_index(
        "ix_study_challenges_user_plan_status_deadline",
        "study_challenges",
        ["user_id", "plan_id", "status", "deadline", "id"],
    )
    op.create_index(
        "ix_study_challenges_plan_subject_activity",
        "study_challenges",
        ["user_id", "plan_id", "subject_id", "activity_id"],
    )
    op.create_index(
        "ix_study_challenges_plan_subject_session",
        "study_challenges",
        ["user_id", "plan_id", "subject_id", "study_session_id"],
    )
    op.create_index(
        "ix_study_challenges_user_subject_activity_session",
        "study_challenges",
        ["user_id", "subject_id", "activity_id", "study_session_id"],
    )
