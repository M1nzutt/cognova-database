"""Separate onboarding and preserve initial perception with append-only responses."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_onboarding_questionnaire"
down_revision = "0002_auth_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Freeze the source while copying legacy data; no concurrent user is missed.
    op.execute("LOCK TABLE users IN ACCESS EXCLUSIVE MODE")
    for column in ("degree_program", "semester", "academic_goal"):
        op.alter_column("users", column, nullable=True)
    # Preserve non-conforming legacy values rather than truncate or reject upgrade.
    # PostgreSQL still enforces NOT VALID checks on all new/updated rows.
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT ck_users_name_registration "
        "CHECK (char_length(btrim(name)) > 0 AND char_length(name) <= 30) NOT VALID"
    )
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT ck_users_email_registration "
        "CHECK (char_length(btrim(email)) > 0 AND char_length(email) <= 50) NOT VALID"
    )
    op.create_table(
        "user_academic_goal_legacy",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        # Preserve even empty strings and unexpected NULL values verbatim.
        sa.Column("academic_goal", sa.Text(), nullable=True),
        sa.Column(
            "captured_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.execute(
        "INSERT INTO user_academic_goal_legacy (user_id, academic_goal) "
        "SELECT id, academic_goal FROM users"
    )
    op.execute("""
        CREATE FUNCTION cognova_valid_questionnaire_answers(payload jsonb)
        RETURNS boolean LANGUAGE plpgsql IMMUTABLE
        SET search_path = pg_catalog AS $$
        DECLARE answer jsonb; item jsonb;
        BEGIN
            IF payload IS NULL OR jsonb_typeof(payload) <> 'object' THEN
                RETURN false;
            END IF;
            IF NOT payload ?& ARRAY['q1','q2','q3','q4','q5','q6','q7','q8','q9','q10']
               OR (SELECT count(*) FROM jsonb_object_keys(payload)) <> 10 THEN
                RETURN false;
            END IF;
            FOR answer IN SELECT value FROM jsonb_each(payload) LOOP
                IF jsonb_typeof(answer) = 'string' THEN
                    IF length(btrim(answer #>> '{}')) = 0 THEN RETURN false; END IF;
                ELSIF jsonb_typeof(answer) = 'array' THEN
                    IF jsonb_array_length(answer) = 0 THEN RETURN false; END IF;
                    FOR item IN SELECT value FROM jsonb_array_elements(answer) LOOP
                        IF jsonb_typeof(item) <> 'string'
                           OR length(btrim(item #>> '{}')) = 0 THEN
                            RETURN false;
                        END IF;
                    END LOOP;
                ELSE RETURN false;
                END IF;
            END LOOP;
            RETURN true;
        END $$
    """)
    op.create_table(
        "questionnaire_responses",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("revision", sa.Integer(), primary_key=True),
        sa.Column("questionnaire_version", sa.Integer(), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("revision > 0", name="ck_questionnaire_revision_positive"),
        sa.CheckConstraint(
            "questionnaire_version > 0", name="ck_questionnaire_version_positive"
        ),
        sa.CheckConstraint(
            "cognova_valid_questionnaire_answers(answers)",
            name="ck_questionnaire_ten_answers",
        ),
    )
    # The composite PK indexes both the first and latest response per user.
    op.execute("""
        CREATE FUNCTION cognova_append_questionnaire() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog AS $$
        DECLARE next_revision integer;
        BEGIN
            -- Schema-qualified dynamic SQL respects injected schema isolation.
            EXECUTE format('SELECT id FROM %I.users WHERE id = $1 FOR UPDATE',
                           TG_TABLE_SCHEMA) USING NEW.user_id;
            EXECUTE format(
                'SELECT coalesce(max(revision), 0) + 1 FROM %I.questionnaire_responses '
                'WHERE user_id = $1', TG_TABLE_SCHEMA)
                INTO next_revision USING NEW.user_id;
            IF NEW.revision <> next_revision THEN
                RAISE EXCEPTION 'Questionnaire revision must be the next revision'
                    USING ERRCODE = '23514';
            END IF;
            NEW.recorded_at := clock_timestamp();
            RETURN NEW;
        END $$
    """)
    op.execute("""
        CREATE FUNCTION cognova_reject_history_change() RETURNS trigger
        LANGUAGE plpgsql SET search_path = pg_catalog AS $$
        BEGIN
            RAISE EXCEPTION 'Historical perception records are immutable'
                USING ERRCODE = '23514';
        END $$
    """)
    op.execute(
        "CREATE TRIGGER questionnaire_append BEFORE INSERT ON questionnaire_responses "
        "FOR EACH ROW EXECUTE FUNCTION cognova_append_questionnaire()"
    )
    for table, events in (
        ("questionnaire_responses", "UPDATE OR DELETE"),
        ("user_academic_goal_legacy", "INSERT OR UPDATE OR DELETE"),
    ):
        op.execute(
            f"CREATE TRIGGER preserve_history BEFORE {events} ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION cognova_reject_history_change()"
        )
        op.execute(
            f"CREATE TRIGGER preserve_history_truncate BEFORE TRUNCATE ON {table} "
            "FOR EACH STATEMENT EXECUTE FUNCTION cognova_reject_history_change()"
        )


def downgrade() -> None:
    # Fail before deleting anything, and exclude racing application writes.
    op.execute(
        "LOCK TABLE users, user_academic_goal_legacy, questionnaire_responses "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM questionnaire_responses) THEN
                RAISE EXCEPTION 'Downgrade blocked: questionnaire history exists';
            END IF;
            IF EXISTS (SELECT 1 FROM users WHERE degree_program IS NULL
                       OR semester IS NULL OR academic_goal IS NULL) THEN
                RAISE EXCEPTION 'Downgrade blocked: users require nullable onboarding';
            END IF;
            IF EXISTS (
                SELECT 1 FROM user_academic_goal_legacy legacy
                LEFT JOIN users ON users.id = legacy.user_id
                WHERE users.id IS NULL
                   OR legacy.academic_goal IS DISTINCT FROM users.academic_goal
            ) THEN
                RAISE EXCEPTION 'Downgrade blocked: legacy goal would be lost';
            END IF;
        END $$
    """)
    op.drop_table("questionnaire_responses")
    op.drop_table("user_academic_goal_legacy")
    op.execute("DROP FUNCTION cognova_append_questionnaire()")
    op.execute("DROP FUNCTION cognova_reject_history_change()")
    op.execute("DROP FUNCTION cognova_valid_questionnaire_answers(jsonb)")
    op.drop_constraint("ck_users_email_registration", "users", type_="check")
    op.drop_constraint("ck_users_name_registration", "users", type_="check")
    for column in ("degree_program", "semester", "academic_goal"):
        op.alter_column("users", column, nullable=False)
