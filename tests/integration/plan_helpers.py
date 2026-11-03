from datetime import datetime, timezone

from alembic import command
from sqlalchemy import text

from cognova_database.runner import migration_config

HEAD = "0007_study_plans_and_challenges"
PREVIOUS = "0006_study_sessions"
START = datetime(2030, 1, 1, 12, tzinfo=timezone.utc)
END = datetime(2030, 1, 8, 12, tzinfo=timezone.utc)


def migrate(connection, revision=HEAD, *, down=False):
    config = migration_config()
    config.attributes["connection"] = connection
    (command.downgrade if down else command.upgrade)(config, revision)


def plan(connection, user_id, **overrides):
    values = dict(
        user_id=user_id,
        name="Exam preparation",
        objective="Prepare for the final exam",
        start_at=START,
        end_at=END,
        status="draft",
        source="ai",
    )
    values.update(overrides)
    columns = ",".join(values)
    parameters = ",".join(f":{name}" for name in values)
    return connection.scalar(
        text(f"INSERT INTO study_plans ({columns}) VALUES ({parameters}) RETURNING id"),
        values,
    )


def study_session(connection, user_id, subject_id, activity_id=None):
    return connection.scalar(
        text(
            "INSERT INTO study_sessions (user_id,subject_id,activity_id,"
            "planned_start_at,planned_duration) VALUES (:uid,:sid,:aid,:planned,30) "
            "RETURNING id"
        ),
        {
            "uid": user_id,
            "sid": subject_id,
            "aid": activity_id,
            "planned": START,
        },
    )


def plan_subject(connection, user_id, plan_id, subject_id):
    connection.execute(
        text(
            "INSERT INTO study_plan_subjects (user_id,plan_id,subject_id) "
            "VALUES (:uid,:plan,:subject)"
        ),
        {"uid": user_id, "plan": plan_id, "subject": subject_id},
    )


def plan_activity(connection, user_id, plan_id, subject_id, activity_id):
    connection.execute(
        text(
            "INSERT INTO study_plan_activities "
            "(user_id,plan_id,subject_id,activity_id) "
            "VALUES (:uid,:plan,:subject,:activity)"
        ),
        {
            "uid": user_id,
            "plan": plan_id,
            "subject": subject_id,
            "activity": activity_id,
        },
    )


def plan_session(connection, user_id, plan_id, subject_id, session_id):
    connection.execute(
        text(
            "INSERT INTO study_plan_sessions "
            "(user_id,plan_id,subject_id,study_session_id) "
            "VALUES (:uid,:plan,:subject,:session)"
        ),
        {
            "uid": user_id,
            "plan": plan_id,
            "subject": subject_id,
            "session": session_id,
        },
    )


def owner_subject(connection, email="owner@test.io"):
    user_id = connection.scalar(
        text(
            "INSERT INTO users (name,email,password_hash) "
            "VALUES ('Test',:email,'fixture') RETURNING id"
        ),
        {"email": email},
    )
    subject_id = connection.scalar(
        text(
            "INSERT INTO subjects (user_id,name,status,difficulty,color_base,"
            "color_shade,active_slot) VALUES (:uid,'Physics','active','easy',"
            "'blue',100,1) RETURNING id"
        ),
        {"uid": user_id},
    )
    return user_id, subject_id
