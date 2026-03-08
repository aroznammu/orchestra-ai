"""add chat_sessions, chat_messages, faq_entries tables

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-03-07 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chat_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=255), server_default='New conversation', nullable=False),
        sa.Column('status', sa.Enum('open', 'resolved', 'closed', name='chatsessionstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_sessions_tenant_id', 'chat_sessions', ['tenant_id'], unique=False)
    op.create_index('ix_chat_sessions_tenant_status', 'chat_sessions', ['tenant_id', 'status'], unique=False)

    op.create_table('chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.Enum('user', 'assistant', 'system', name='chatmessagerole'), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'], unique=False)
    op.create_index('ix_chat_messages_session_created', 'chat_messages', ['session_id', 'created_at'], unique=False)

    op.create_table('faq_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=True),
        sa.Column('category', sa.String(length=100), server_default='General', nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_published', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_faq_tenant_category_published', 'faq_entries', ['tenant_id', 'category', 'is_published'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_faq_tenant_category_published', table_name='faq_entries')
    op.drop_table('faq_entries')

    op.drop_index('ix_chat_messages_session_created', table_name='chat_messages')
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_table('chat_messages')

    op.drop_index('ix_chat_sessions_tenant_status', table_name='chat_sessions')
    op.drop_index('ix_chat_sessions_tenant_id', table_name='chat_sessions')
    op.drop_table('chat_sessions')

    op.execute("DROP TYPE IF EXISTS chatsessionstatus")
    op.execute("DROP TYPE IF EXISTS chatmessagerole")
