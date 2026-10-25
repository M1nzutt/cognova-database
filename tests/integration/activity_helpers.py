from datetime import datetime, timezone

from alembic import command
from sqlalchemy import text

from cognova_database.runner import migration_config

PREVIOUS = "0004_subjects"
HEAD = "0005_activities"
DEADLINE = datetime(2030, 1, 1, 12, tzinfo=timezone.utc)


def migrate(connection, revision=HEAD, *, down=False):
    config = migration_config()
    config.attributes["connection"] = connection
    (command.downgrade if down else command.upgrade)(config, revision)


def owner_subject(c, suffix="one"):
    uid = c.scalar(
        text(
            "INSERT INTO users (name,email,password_hash) "
            "VALUES ('Test',:email,'fixture') RETURNING id"
        ),
        {"email": suffix + "@test.io"},
    )
    sid = c.scalar(
        text(
            "INSERT INTO subjects (user_id,name,status,difficulty,color_base,"
            "color_shade,active_slot) VALUES (:uid,'Test','active','easy','blue',"
            "100,1) RETURNING id"
        ),
        {"uid": uid},
    )
    return uid, sid


def activity(c, uid, sid, **overrides):
    values = dict(
        user_id=uid,
        subject_id=sid,
        title="Activity",
        deadline=DEADLINE,
        priority="medium",
        status="pending",
        estimated_duration=30,
        notes=None,
    )
    values.update(overrides)
    columns = ",".join(values)
    params = ",".join(":" + name for name in values)
    return c.scalar(
        text(f"INSERT INTO activities ({columns}) VALUES ({params}) RETURNING id"),
        values,
    )
