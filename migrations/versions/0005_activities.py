"""Activities with same-owner subjects and automatic immutable deadline events."""

import sqlalchemy as sa
from alembic import op

revision = "0005_activities"
down_revision = "0004_subjects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL requires a unique referenced key for the composite ownership FK.
    op.create_unique_constraint("uq_subjects_user_id_id", "subjects", ["user_id", "id"])
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("original_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "deadline_revision", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("estimated_duration", sa.SmallInteger(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
            ["user_id", "subject_id"],
            ["subjects.user_id", "subjects.id"],
            name="fk_activities_owner_subject",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint(
            "char_length(title) BETWEEN 1 AND 50 AND title = btrim(title) "
            "AND title !~ '^[[:space:]]*$'",
            name="ck_activities_title",
        ),
        sa.CheckConstraint("isfinite(deadline)", name="ck_activities_deadline"),
        sa.CheckConstraint(
            "isfinite(original_deadline)",
            name="ck_activities_original_deadline",
        ),
        sa.CheckConstraint("deadline_revision >= 0", name="ck_activities_revision"),
        sa.CheckConstraint(
            "priority IN ('low','medium','high','urgent')",
            name="ck_activities_priority",
        ),
        sa.CheckConstraint(
            "status IN ('pending','in_progress','completed','postponed','cancelled')",
            name="ck_activities_status",
        ),
        sa.CheckConstraint(
            "estimated_duration BETWEEN 10 AND 300",
            name="ck_activities_duration",
        ),
        sa.CheckConstraint("char_length(notes) <= 200", name="ck_activities_notes"),
        sa.CheckConstraint(
            "isfinite(created_at) AND isfinite(updated_at) "
            "AND updated_at >= created_at",
            name="ck_activities_timestamps",
        ),
    )
    op.create_index(
        "ix_activities_user_subject", "activities", ["user_id", "subject_id"]
    )
    op.create_index(
        "ix_activities_user_status_deadline",
        "activities",
        ["user_id", "status", "deadline", "id"],
    )
    op.create_table(
        "activity_deadline_events",
        sa.Column("activity_id", sa.Integer(), primary_key=True),
        sa.Column("revision", sa.Integer(), primary_key=True),
        sa.Column("previous_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("new_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["activities.id"],
            name="fk_deadline_events_activity",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint("revision > 0", name="ck_deadline_events_revision"),
        sa.CheckConstraint(
            "isfinite(previous_deadline) AND isfinite(new_deadline) "
            "AND isfinite(occurred_at)",
            name="ck_deadline_events_finite",
        ),
        sa.CheckConstraint(
            "(event_type = 'postponed' AND new_deadline > previous_deadline) "
            "OR (event_type = 'rescheduled' AND new_deadline < previous_deadline)",
            name="ck_deadline_events_direction",
        ),
    )
    op.execute("""
        CREATE FUNCTION cognova_prepare_activity() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                IF (NEW.original_deadline IS NOT NULL AND
                    NEW.original_deadline IS DISTINCT FROM NEW.deadline)
                   OR NEW.deadline_revision IS DISTINCT FROM 0 THEN
                    RAISE EXCEPTION 'Invalid initial activity metadata'
                        USING ERRCODE = '23514';
                END IF;
                NEW.original_deadline := NEW.deadline;
                NEW.created_at := clock_timestamp();
                NEW.updated_at := NEW.created_at;
            ELSE
                IF NEW.id IS DISTINCT FROM OLD.id
                   OR NEW.user_id IS DISTINCT FROM OLD.user_id
                   OR NEW.created_at IS DISTINCT FROM OLD.created_at
                   OR NEW.original_deadline IS DISTINCT FROM OLD.original_deadline
                   OR NEW.deadline_revision IS DISTINCT FROM OLD.deadline_revision THEN
                    RAISE EXCEPTION 'Activity identity/history metadata are immutable'
                        USING ERRCODE = '23514';
                END IF;
                NEW.updated_at := greatest(clock_timestamp(), OLD.updated_at);
                IF NEW.deadline IS DISTINCT FROM OLD.deadline THEN
                    NEW.deadline_revision := OLD.deadline_revision + 1;
                END IF;
            END IF;
            RETURN NEW;
        END $$
    """)
    # Runtime need not INSERT history or EXECUTE this function. Trigger invocation
    # uses the migration owner's rights; all object references are schema-qualified.
    op.execute("""
        CREATE FUNCTION cognova_record_activity_deadline() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
        BEGIN
            IF NEW.deadline IS DISTINCT FROM OLD.deadline THEN
                EXECUTE format(
                    'INSERT INTO %I.activity_deadline_events '
                    '(activity_id,revision,previous_deadline,new_deadline,'
                    'event_type,occurred_at) VALUES ($1,$2,$3,$4,$5,$6)',
                    TG_TABLE_SCHEMA)
                USING NEW.id, NEW.deadline_revision, OLD.deadline, NEW.deadline,
                    CASE WHEN NEW.deadline > OLD.deadline THEN 'postponed'
                         ELSE 'rescheduled' END, NEW.updated_at;
            END IF;
            RETURN NEW;
        END $$
    """)
    op.execute("""
        CREATE FUNCTION cognova_preserve_activity_deadline() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog AS $$
        BEGIN
            RAISE EXCEPTION 'Activity deadline history is immutable'
                USING ERRCODE = '23514';
        END $$
    """)
    op.execute(
        "CREATE TRIGGER activity_prepare BEFORE INSERT OR UPDATE ON activities "
        "FOR EACH ROW EXECUTE FUNCTION cognova_prepare_activity()"
    )
    op.execute(
        "CREATE TRIGGER activity_record_deadline AFTER UPDATE ON activities "
        "FOR EACH ROW EXECUTE FUNCTION cognova_record_activity_deadline()"
    )
    op.execute(
        "CREATE TRIGGER deadline_events_immutable BEFORE UPDATE OR DELETE "
        "ON activity_deadline_events FOR EACH ROW "
        "EXECUTE FUNCTION cognova_preserve_activity_deadline()"
    )
    op.execute(
        "CREATE TRIGGER deadline_events_no_truncate BEFORE TRUNCATE "
        "ON activity_deadline_events FOR EACH STATEMENT "
        "EXECUTE FUNCTION cognova_preserve_activity_deadline()"
    )
    for function in (
        "cognova_prepare_activity",
        "cognova_record_activity_deadline",
        "cognova_preserve_activity_deadline",
    ):
        op.execute(f"REVOKE ALL ON FUNCTION {function}() FROM PUBLIC")
    op.execute("REVOKE ALL ON activities, activity_deadline_events FROM PUBLIC")


def downgrade() -> None:
    op.execute(
        "LOCK TABLE subjects, activities, activity_deadline_events "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM activities)
               OR EXISTS (SELECT 1 FROM activity_deadline_events) THEN
                RAISE EXCEPTION 'Downgrade blocked: activity data or history exist';
            END IF;
        END $$
    """)
    # Never CASCADE; unknown future dependencies cause an atomic failure.
    op.drop_table("activity_deadline_events")
    op.drop_table("activities")
    op.execute("DROP FUNCTION cognova_preserve_activity_deadline()")
    op.execute("DROP FUNCTION cognova_record_activity_deadline()")
    op.execute("DROP FUNCTION cognova_prepare_activity()")
    op.drop_constraint("uq_subjects_user_id_id", "subjects", type_="unique")
