"""Persist the current visible AI proposal for a study plan."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_ai_plan_proposal_snapshot"
down_revision = "0007_study_plans_and_challenges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "study_plans",
        sa.Column("ai_proposal_snapshot", postgresql.JSONB(), nullable=True),
    )
    op.create_check_constraint(
        "ck_study_plans_ai_proposal_snapshot",
        "study_plans",
        "ai_proposal_snapshot IS NULL OR "
        "(jsonb_typeof(ai_proposal_snapshot) = 'object' "
        "AND octet_length(ai_proposal_snapshot::text) <= 32768)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_study_plans_ai_proposal_snapshot", "study_plans", type_="check"
    )
    op.drop_column("study_plans", "ai_proposal_snapshot")
