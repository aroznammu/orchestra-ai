"""add kill_switch_events table

Revision ID: a2b3c4d5e6f7
Revises: f1ee2468d878
Create Date: 2026-02-28 23:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = 'f1ee2468d878'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('kill_switch_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('triggered_by', sa.String(length=255), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('affected_platforms', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('affected_campaigns', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kill_switch_events_tenant_id'), 'kill_switch_events', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_kill_switch_events_created_at'), 'kill_switch_events', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_kill_switch_events_created_at'), table_name='kill_switch_events')
    op.drop_index(op.f('ix_kill_switch_events_tenant_id'), table_name='kill_switch_events')
    op.drop_table('kill_switch_events')
