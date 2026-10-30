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
    _integrity()
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
    op.execute("DROP FUNCTION cognova_validate_study_execution()")
    op.execute("DROP FUNCTION cognova_prepare_study_interval()")
    op.execute("DROP FUNCTION cognova_prepare_study_session()")
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


def _integrity() -> None:
    op.execute("""
        CREATE FUNCTION cognova_prepare_study_session() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                NEW.created_at := clock_timestamp();
                NEW.updated_at := NEW.created_at;
            ELSE
                IF NEW.id IS DISTINCT FROM OLD.id
                   OR NEW.user_id IS DISTINCT FROM OLD.user_id
                   OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
                    RAISE EXCEPTION 'Study session identity is immutable'
                        USING ERRCODE = '23514';
                END IF;
                NEW.updated_at := greatest(clock_timestamp(), OLD.updated_at);
            END IF;
            RETURN NEW;
        END $$
    """)
    op.execute("""
        CREATE FUNCTION cognova_prepare_study_interval() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog AS $$
        DECLARE parent_id integer;
        BEGIN
            IF TG_OP IN ('DELETE','TRUNCATE') THEN
                RAISE EXCEPTION 'Study execution evidence cannot be removed'
                    USING ERRCODE = '23514';
            END IF;
            IF TG_OP = 'INSERT' THEN
                NEW.created_at := clock_timestamp();
                NEW.updated_at := NEW.created_at;
            ELSE
                IF NEW.id IS DISTINCT FROM OLD.id
                   OR NEW.session_id IS DISTINCT FROM OLD.session_id
                   OR NEW.started_at IS DISTINCT FROM OLD.started_at
                   OR NEW.created_at IS DISTINCT FROM OLD.created_at
                   OR (OLD.ended_at IS NOT NULL
                       AND NEW.ended_at IS DISTINCT FROM OLD.ended_at) THEN
                    RAISE EXCEPTION 'Study interval evidence is immutable'
                        USING ERRCODE = '23514';
                END IF;
                NEW.updated_at := greatest(clock_timestamp(), OLD.updated_at);
            END IF;
            -- Metadata-only write serializes parent/child validation, including
            -- REPEATABLE READ. Never change timer fields or calculate duration.
            EXECUTE format('UPDATE %I.study_sessions SET updated_at=updated_at '
                           'WHERE id=$1 RETURNING id', TG_TABLE_SCHEMA)
                INTO parent_id USING NEW.session_id;
            IF parent_id IS NULL THEN
                RAISE EXCEPTION 'Study session does not exist'
                    USING ERRCODE = '23503';
            END IF;
            RETURN NEW;
        END $$
    """)
    op.execute("""
        CREATE FUNCTION cognova_validate_study_execution() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog AS $$
        DECLARE
            session_key integer;
            s record;
            evidence record;
        BEGIN
            IF TG_TABLE_NAME = 'study_sessions' THEN
                session_key := NEW.id;
            ELSE
                session_key := NEW.session_id;
            END IF;
            EXECUTE format('SELECT * FROM %I.study_sessions WHERE id=$1',
                           TG_TABLE_SCHEMA) INTO s USING session_key;
            IF s.id IS NULL THEN
                RETURN NULL;
            END IF;
            EXECUTE format(
                'SELECT count(*) AS total, '
                'count(*) FILTER (WHERE ended_at IS NULL) AS opened, '
                'min(started_at) AS first_start, max(ended_at) AS last_end '
                'FROM %I.study_session_intervals WHERE session_id=$1',
                TG_TABLE_SCHEMA) INTO evidence USING session_key;
            IF (evidence.total > 0 AND
                (s.start_at IS NULL OR evidence.first_start <> s.start_at
                 OR (s.end_at IS NOT NULL AND evidence.last_end > s.end_at)))
               OR (s.execution_state = 'planned' AND evidence.total <> 0)
               OR (s.execution_state = 'running' AND evidence.opened <> 1)
               OR (s.execution_state = 'paused' AND
                   (evidence.total = 0 OR evidence.opened <> 0))
               OR (s.execution_state = 'finished' AND
                   (evidence.opened <> 0
                    OR (s.start_at IS NULL AND evidence.total <> 0)
                    OR (s.start_at IS NOT NULL AND evidence.total = 0))) THEN
                RAISE EXCEPTION 'Study execution evidence is inconsistent'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NULL;
        END $$
    """)
    op.execute(
        "CREATE TRIGGER study_session_prepare BEFORE INSERT OR UPDATE "
        "ON study_sessions FOR EACH ROW "
        "EXECUTE FUNCTION cognova_prepare_study_session()"
    )
    op.execute(
        "CREATE TRIGGER study_interval_prepare BEFORE INSERT OR UPDATE OR DELETE "
        "ON study_session_intervals FOR EACH ROW "
        "EXECUTE FUNCTION cognova_prepare_study_interval()"
    )
    op.execute(
        "CREATE TRIGGER study_interval_no_truncate BEFORE TRUNCATE "
        "ON study_session_intervals FOR EACH STATEMENT "
        "EXECUTE FUNCTION cognova_prepare_study_interval()"
    )
    for table in ("study_sessions", "study_session_intervals"):
        op.execute(
            f"CREATE CONSTRAINT TRIGGER {table}_execution_valid "
            f"AFTER INSERT OR UPDATE ON {table} DEFERRABLE INITIALLY DEFERRED "
            "FOR EACH ROW EXECUTE FUNCTION cognova_validate_study_execution()"
        )
    for function in (
        "cognova_prepare_study_session",
        "cognova_prepare_study_interval",
        "cognova_validate_study_execution",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION {function}() FROM PUBLIC")
