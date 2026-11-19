import pytest
from alembic import command
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from cognova_database.runner import migration_config
from tests.integration.test_migrations import insert_user, upgrade

pytestmark = pytest.mark.integration


def test_chat_owner_relationship_limits_and_data_preserving_downgrade(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        upgrade(connection, "head")
        owner_id = insert_user(connection, "chat-owner@example.com")
        other_id = insert_user(connection, "chat-other@example.com")
        conversation_id = connection.scalar(
            text(
                "INSERT INTO academic_conversations(user_id,title) "
                "VALUES (:user_id,'Conversación privada') RETURNING id"
            ),
            {"user_id": owner_id},
        )
        connection.execute(
            text(
                "INSERT INTO academic_messages "
                "(user_id,conversation_id,role,content,evidence) "
                "VALUES (:user_id,:conversation_id,'user','¿Qué priorizo?','[]')"
            ),
            {"user_id": owner_id, "conversation_id": conversation_id},
        )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                text(
                    "INSERT INTO academic_messages "
                    "(user_id,conversation_id,role,content,evidence) "
                    "VALUES (:user_id,:conversation_id,'assistant','No autorizado',"
                    "'[]')"
                ),
                {"user_id": other_id, "conversation_id": conversation_id},
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                text(
                    "INSERT INTO academic_messages "
                    "(user_id,conversation_id,role,content,evidence) "
                    "VALUES (:user_id,:conversation_id,'user',:content,'[]')"
                ),
                {
                    "user_id": owner_id,
                    "conversation_id": conversation_id,
                    "content": "x" * 4001,
                },
            )
        assert connection.scalar(
            text("SELECT count(*) FROM academic_messages WHERE user_id=:owner"),
            {"owner": owner_id},
        ) == 1

        config = migration_config()
        config.attributes["connection"] = connection
        with (
            pytest.raises(Exception, match="Downgrade blocked"),
            connection.begin_nested(),
        ):
            command.downgrade(config, "0008_ai_plan_proposal_snapshot")
        assert connection.scalar(
            text("SELECT version_num FROM alembic_version")
        ) == "0010_nullable_password_hash"
        assert connection.scalar(
            text("SELECT count(*) FROM academic_conversations")
        ) == 1
