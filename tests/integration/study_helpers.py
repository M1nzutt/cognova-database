from datetime import datetime, timedelta, timezone

from alembic import command
from sqlalchemy import text

from cognova_database.runner import migration_config

HEAD = "0006_study_sessions"
PREVIOUS = "0005_activities"
START = datetime(2030, 1, 1, 12, tzinfo=timezone.utc)
END = START + timedelta(minutes=30)


def migrate(c, revision=HEAD, *, down=False):
    config = migration_config()
    config.attributes["connection"] = c
    (command.downgrade if down else command.upgrade)(config, revision)


def session(c, uid, sid, **overrides):
    values = dict(
        user_id=uid, subject_id=sid, planned_start_at=START, planned_duration=30
    )
    values.update(overrides)
    return c.scalar(
        text(
            "INSERT INTO study_sessions ("
            + ",".join(values)
            + ") VALUES ("
            + ",".join(":" + name for name in values)
            + ") RETURNING id"
        ),
        values,
    )


def interval(c, session_id, start=START, end=None):
    return c.scalar(
        text(
            "INSERT INTO study_session_intervals (session_id,started_at,ended_at) "
            "VALUES (:id,:start,:end) RETURNING id"
        ),
        dict(id=session_id, start=start, end=end),
    )


def validate(c):
    c.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    c.execute(text("SET CONSTRAINTS ALL DEFERRED"))


def running(c, uid, sid):
    key = session(c, uid, sid, execution_state="running", start_at=START)
    interval(c, key)
    validate(c)
    return key
