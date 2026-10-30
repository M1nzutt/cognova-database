"""Study session planning, execution evidence and restrictive dependencies."""

import sqlalchemy as sa
from alembic import op

revision = "0006_study_sessions"
down_revision = "0005_activities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "study_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=True),
        sa.Column("planned_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("planned_duration", sa.SmallInteger(), nullable=False),
        sa.Column(
            "execution_state", sa.Text(), nullable=False, server_default="planned"
        ),
        sa.Column("status", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "actual_duration", sa.Numeric(20, 6), nullable=False, server_default="0"
        ),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("other_text", sa.Text(), nullable=True),
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
        sa.CheckConstraint(
            "isfinite(planned_start_at)", name="ck_study_sessions_planned_start"
        ),
        sa.CheckConstraint(
            "planned_duration BETWEEN 10 AND 180",
            name="ck_study_sessions_planned_duration",
        ),
        sa.CheckConstraint(
            "execution_state IN ('planned','running','paused','finished')",
            name="ck_study_sessions_execution_state",
        ),
        sa.CheckConstraint(
            "status IN ('completed','partial','postponed','cancelled')",
            name="ck_study_sessions_status",
        ),
        sa.CheckConstraint(
            "(start_at IS NULL OR isfinite(start_at)) AND "
            "(end_at IS NULL OR (isfinite(end_at) AND start_at IS NOT NULL "
            "AND end_at > start_at))",
            name="ck_study_sessions_execution_times",
        ),
        sa.CheckConstraint(
            "actual_duration >= 0 AND actual_duration < 'Infinity'::numeric",
            name="ck_study_sessions_actual_duration",
        ),
        sa.CheckConstraint(
            "context IN ('finished_early','distracted','tired','interrupted',"
            "'changed_activity','other')",
            name="ck_study_sessions_context",
        ),
        sa.CheckConstraint(
            "(context IS NOT DISTINCT FROM 'other' AND other_text IS NOT NULL "
            "AND char_length(other_text) BETWEEN 1 AND 200 "
            "AND other_text = btrim(other_text) "
            "AND other_text !~ '^[[:space:]]*$') OR "
            "(context IS DISTINCT FROM 'other' AND other_text IS NULL)",
            name="ck_study_sessions_other_text",
        ),
        sa.CheckConstraint(
            "(execution_state = 'planned' AND start_at IS NULL "
            "AND end_at IS NULL AND actual_duration = 0 AND status IS NULL "
            "AND context IS NULL) OR "
            "(execution_state IN ('running','paused') AND start_at IS NOT NULL "
            "AND end_at IS NULL AND status IS NULL AND context IS NULL) OR "
            "(execution_state = 'finished' AND status IS NOT NULL AND ("
            "(start_at IS NOT NULL AND end_at IS NOT NULL AND actual_duration > 0) "
            "OR (status IN ('postponed','cancelled') AND start_at IS NULL "
            "AND end_at IS NULL AND actual_duration = 0)))",
            name="ck_study_sessions_lifecycle",
        ),
        sa.CheckConstraint(
            "isfinite(created_at) AND isfinite(updated_at) "
            "AND updated_at >= created_at",
            name="ck_study_sessions_timestamps",
        ),
    )
    op.create_table(
        "study_session_intervals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "isfinite(started_at) AND "
            "(ended_at IS NULL OR (isfinite(ended_at) AND ended_at > started_at))",
            name="ck_study_intervals_times",
        ),
        sa.CheckConstraint(
            "isfinite(created_at) AND isfinite(updated_at) "
            "AND updated_at >= created_at",
            name="ck_study_intervals_timestamps",
        ),
    )
    _references()
    _indexes()
    op.execute("REVOKE ALL ON study_sessions, study_session_intervals FROM PUBLIC")
    op.execute(
        "REVOKE ALL ON SEQUENCE study_sessions_id_seq, "
        "study_session_intervals_id_seq FROM PUBLIC"
    )


def downgrade() -> None:
    op.execute(
        "LOCK TABLE subjects, activities, study_sessions, study_session_intervals "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM study_sessions)
               OR EXISTS (SELECT 1 FROM study_session_intervals) THEN
                RAISE EXCEPTION 'Downgrade blocked: study session evidence exists';
            END IF;
        END $$
    """)
    op.drop_table("study_session_intervals")
    op.drop_table("study_sessions")
    op.drop_constraint("uq_activities_user_subject_id", "activities", type_="unique")


def _references() -> None:
    op.create_unique_constraint(
        "uq_activities_user_subject_id", "activities", ["user_id", "subject_id", "id"]
    )
    op.create_foreign_key(
        "fk_study_sessions_owner_subject",
        "study_sessions",
        "subjects",
        ["user_id", "subject_id"],
        ["user_id", "id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_foreign_key(
        "fk_study_sessions_owner_subject_activity",
        "study_sessions",
        "activities",
        ["user_id", "subject_id", "activity_id"],
        ["user_id", "subject_id", "id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_foreign_key(
        "fk_study_intervals_session",
        "study_session_intervals",
        "study_sessions",
        ["session_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def _indexes() -> None:
    op.create_index(
        "ix_study_sessions_user_planned",
        "study_sessions",
        ["user_id", "planned_start_at", "id"],
    )
    op.create_index(
        "ix_study_sessions_owner_activity",
        "study_sessions",
        ["user_id", "subject_id", "activity_id"],
    )
    op.create_index(
        "uq_study_sessions_user_executing",
        "study_sessions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("execution_state IN ('running','paused')"),
    )
    op.create_index(
        "ix_study_intervals_session_started",
        "study_session_intervals",
        ["session_id", "started_at", "id"],
    )
    op.create_index(
        "uq_study_intervals_open",
        "study_session_intervals",
        ["session_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )
    # Built-in range opclasses: no extension or superuser installation needed.
    op.execute("""
        ALTER TABLE study_session_intervals ADD CONSTRAINT ex_study_intervals_overlap
        EXCLUDE USING gist (
            int8range(session_id::bigint, session_id::bigint, '[]') WITH &&,
            tstzrange(started_at, ended_at, '[)') WITH &&
        )
    """)
