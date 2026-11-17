"""Persist owner-scoped academic companion conversations and messages."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_academic_companion_chat"
down_revision = "0008_ai_plan_proposal_snapshot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "academic_conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(title) BETWEEN 1 AND 80 AND title = btrim(title) "
            "AND title !~ '^[[:space:]]*$'",
            name="ck_academic_conversations_title",
        ),
        sa.CheckConstraint(
            "isfinite(created_at) AND isfinite(updated_at) "
            "AND updated_at >= created_at",
            name="ck_academic_conversations_timestamps",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_academic_conversations_user",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_academic_conversations"),
        sa.UniqueConstraint(
            "user_id", "id", name="uq_academic_conversations_user_id_id"
        ),
    )
    op.create_index(
        "ix_academic_conversations_user_updated",
        "academic_conversations",
        ["user_id", "updated_at", "id"],
    )
    op.create_table(
        "academic_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('user','assistant')", name="ck_academic_messages_role"
        ),
        sa.CheckConstraint(
            "(role = 'user' AND char_length(content) BETWEEN 1 AND 4000 "
            "AND jsonb_typeof(evidence) = 'array' AND evidence = '[]'::jsonb) OR "
            "(role = 'assistant' AND char_length(content) BETWEEN 1 AND 3000 "
            "AND jsonb_typeof(evidence) = 'array' "
            "AND octet_length(evidence::text) <= 8192)",
            name="ck_academic_messages_content_evidence",
        ),
        sa.CheckConstraint(
            "isfinite(created_at)", name="ck_academic_messages_created_at"
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "conversation_id"],
            ["academic_conversations.user_id", "academic_conversations.id"],
            ondelete="CASCADE",
            name="fk_academic_messages_owner_conversation",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_academic_messages"),
    )
    op.create_index(
        "ix_academic_messages_user_conversation_id",
        "academic_messages",
        ["user_id", "conversation_id", "id"],
    )
    op.execute(
        "REVOKE ALL ON TABLE academic_conversations, academic_messages FROM PUBLIC"
    )
    op.execute(
        "REVOKE ALL ON SEQUENCE academic_conversations_id_seq, "
        "academic_messages_id_seq FROM PUBLIC"
    )


def downgrade() -> None:
    op.execute(
        "LOCK TABLE academic_conversations, academic_messages "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM academic_messages)
               OR EXISTS (SELECT 1 FROM academic_conversations) THEN
                RAISE EXCEPTION 'Downgrade blocked: academic conversation data exists';
            END IF;
        END $$
    """)
    op.drop_index(
        "ix_academic_messages_user_conversation_id", table_name="academic_messages"
    )
    op.drop_table("academic_messages")
    op.drop_index(
        "ix_academic_conversations_user_updated",
        table_name="academic_conversations",
    )
    op.drop_table("academic_conversations")
