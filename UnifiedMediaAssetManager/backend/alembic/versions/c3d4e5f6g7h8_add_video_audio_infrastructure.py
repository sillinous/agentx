"""add_video_audio_infrastructure

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create video_jobs table
    op.create_table(
        'video_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('universe_id', sa.String(), nullable=True),
        sa.Column('agent_job_id', sa.String(), nullable=True),

        # Request parameters
        sa.Column('generation_type', sa.String(length=50), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('negative_prompt', sa.Text(), nullable=True),
        sa.Column('reference_image_url', sa.Text(), nullable=True),

        # Strategy parameters
        sa.Column('mood_category', sa.String(length=50), nullable=True),
        sa.Column('camera_movement', sa.String(length=100), nullable=True),
        sa.Column('aspect_ratio', sa.String(length=10), nullable=False, server_default='16:9'),
        sa.Column('duration', sa.Integer(), nullable=False, server_default='5'),

        # External API details
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('provider_job_id', sa.String(length=255), nullable=True),
        sa.Column('provider_status', sa.String(length=50), nullable=True),

        # Generated content
        sa.Column('video_url', sa.Text(), nullable=True),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('local_path', sa.Text(), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),

        # Metadata
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['universe_id'], ['universes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_job_id'], ['agent_jobs.id'], ondelete='SET NULL')
    )

    # Create indexes for video_jobs
    op.create_index('idx_video_jobs_universe', 'video_jobs', ['universe_id'])
    op.create_index('idx_video_jobs_status', 'video_jobs', ['status'])
    op.create_index('idx_video_jobs_provider', 'video_jobs', ['provider', 'provider_job_id'])
    op.create_index('idx_video_jobs_created', 'video_jobs', ['created_at'])

    # Create audio_jobs table
    op.create_table(
        'audio_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('universe_id', sa.String(), nullable=True),
        sa.Column('agent_job_id', sa.String(), nullable=True),

        # Request parameters
        sa.Column('generation_type', sa.String(length=50), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=True),
        sa.Column('audio_input_path', sa.Text(), nullable=True),

        # Generation parameters
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('voice_id', sa.String(length=255), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),

        # External API details
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('provider_job_id', sa.String(length=255), nullable=True),

        # Generated content
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('local_path', sa.Text(), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('transcription', sa.JSON(), nullable=True),

        # Metadata
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['universe_id'], ['universes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_job_id'], ['agent_jobs.id'], ondelete='SET NULL')
    )

    # Create indexes for audio_jobs
    op.create_index('idx_audio_jobs_universe', 'audio_jobs', ['universe_id'])
    op.create_index('idx_audio_jobs_status', 'audio_jobs', ['status'])
    op.create_index('idx_audio_jobs_created', 'audio_jobs', ['created_at'])

    # Create media_assets table
    op.create_table(
        'media_assets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('universe_id', sa.String(), nullable=True),
        sa.Column('element_id', sa.String(), nullable=True),

        # Asset details
        sa.Column('asset_type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        # File details
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('public_url', sa.Text(), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('dimensions', sa.JSON(), nullable=True),

        # Source tracking
        sa.Column('source_job_id', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=True),

        # Metadata
        sa.Column('tags', sa.JSON(), nullable=True),  # Store as JSON for SQLite compatibility
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['universe_id'], ['universes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['element_id'], ['elements.id'], ondelete='SET NULL')
    )

    # Create indexes for media_assets
    op.create_index('idx_media_assets_universe', 'media_assets', ['universe_id'])
    op.create_index('idx_media_assets_type', 'media_assets', ['asset_type'])
    op.create_index('idx_media_assets_element', 'media_assets', ['element_id'])
    op.create_index('idx_media_assets_created', 'media_assets', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_media_assets_created', table_name='media_assets')
    op.drop_index('idx_media_assets_element', table_name='media_assets')
    op.drop_index('idx_media_assets_type', table_name='media_assets')
    op.drop_index('idx_media_assets_universe', table_name='media_assets')
    op.drop_table('media_assets')

    op.drop_index('idx_audio_jobs_created', table_name='audio_jobs')
    op.drop_index('idx_audio_jobs_status', table_name='audio_jobs')
    op.drop_index('idx_audio_jobs_universe', table_name='audio_jobs')
    op.drop_table('audio_jobs')

    op.drop_index('idx_video_jobs_created', table_name='video_jobs')
    op.drop_index('idx_video_jobs_provider', table_name='video_jobs')
    op.drop_index('idx_video_jobs_status', table_name='video_jobs')
    op.drop_index('idx_video_jobs_universe', table_name='video_jobs')
    op.drop_table('video_jobs')
