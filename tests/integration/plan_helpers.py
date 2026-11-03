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
