"""add agent infrastructure

Revision ID: b2c3d4e5f6g7
Revises: ab1f7db08fb0
Create Date: 2026-01-03 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'ab1f7db08fb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agent_jobs table
    op.create_table(
        'agent_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('universe_id', sa.String(), nullable=True),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('input_data', sa.JSON(), nullable=False),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('human_review_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['universe_id'], ['universes.id'], ondelete='CASCADE'),
    )

    # Create indexes for agent_jobs
    op.create_index('idx_agent_jobs_universe', 'agent_jobs', ['universe_id'])
    op.create_index('idx_agent_jobs_status', 'agent_jobs', ['status'])
    op.create_index('idx_agent_jobs_type', 'agent_jobs', ['agent_type'])
    op.create_index('idx_agent_jobs_created', 'agent_jobs', ['created_at'])

    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('preference_key', sa.String(length=100), nullable=False),
        sa.Column('preference_value', sa.JSON(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for user_preferences
    op.create_index('idx_user_prefs_user', 'user_preferences', ['user_id'])
    op.create_index('idx_user_prefs_key', 'user_preferences', ['preference_key'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_user_prefs_key', table_name='user_preferences')
    op.drop_index('idx_user_prefs_user', table_name='user_preferences')
    op.drop_index('idx_agent_jobs_created', table_name='agent_jobs')
    op.drop_index('idx_agent_jobs_type', table_name='agent_jobs')
    op.drop_index('idx_agent_jobs_status', table_name='agent_jobs')
    op.drop_index('idx_agent_jobs_universe', table_name='agent_jobs')

    # Drop tables
    op.drop_table('user_preferences')
    op.drop_table('agent_jobs')
