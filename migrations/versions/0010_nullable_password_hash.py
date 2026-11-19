"""Allow demo accounts to ship without a reusable password credential."""

import sqlalchemy as sa
from alembic import op

revision = "0010_nullable_password_hash"
down_revision = "0009_academic_companion_chat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM users WHERE password_hash IS NULL) THEN "
        "RAISE EXCEPTION 'Cannot require passwords while passwordless accounts exist'; "
        "END IF; END $$"
    )
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.Text(),
        nullable=False,
    )
