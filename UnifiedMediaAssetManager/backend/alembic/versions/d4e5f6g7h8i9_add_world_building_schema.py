"""add_world_building_schema

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-04 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create world_configs table
    op.create_table(
        'world_configs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('universe_id', sa.String(), nullable=False),

        # Core Parameters
        sa.Column('genre', sa.String(length=100), nullable=False),
        sa.Column('physics', sa.String(length=100), nullable=True),
        sa.Column('magic_system', sa.String(length=100), nullable=True),
        sa.Column('tech_level', sa.String(length=100), nullable=True),
        sa.Column('tone', sa.String(length=100), nullable=True),

        # Extended Configuration (JSON for flexibility)
        sa.Column('color_palette', sa.JSON(), nullable=True),
        sa.Column('art_style_notes', sa.Text(), nullable=True),
        sa.Column('reference_images', sa.JSON(), nullable=True),

        # Metadata
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['universe_id'], ['universes.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('universe_id', name='uq_world_configs_universe')
    )
    op.create_index('idx_world_configs_universe', 'world_configs', ['universe_id'])

    # Create entity_traits table
    op.create_table(
        'entity_traits',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('element_id', sa.String(), nullable=False),

        # Trait Definition
        sa.Column('trait_key', sa.String(length=100), nullable=False),
        sa.Column('trait_value', sa.Text(), nullable=True),
        sa.Column('trait_type', sa.String(length=50), nullable=True),  # 'text', 'number', 'boolean', 'list', 'json'
        sa.Column('trait_category', sa.String(length=50), nullable=True),  # 'core', 'physical', 'behavioral', etc.

        # Display & AI Settings
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_ai_visible', sa.Boolean(), nullable=False, server_default='true'),

        # Metadata
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['element_id'], ['elements.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('element_id', 'trait_key', name='uq_entity_traits_element_key')
    )
    op.create_index('idx_entity_traits_element', 'entity_traits', ['element_id'])
    op.create_index('idx_entity_traits_key', 'entity_traits', ['element_id', 'trait_key'])

    # Create timeline_events table
    op.create_table(
        'timeline_events',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('universe_id', sa.String(), nullable=False),

        # Event Details
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=True),  # 'battle', 'discovery', 'meeting', etc.

        # Relationships (JSON arrays of element IDs)
        sa.Column('participants', sa.JSON(), nullable=True),  # Array of element IDs
        sa.Column('location_id', sa.String(), nullable=True),

        # Impact & Consequences
        sa.Column('significance', sa.String(length=20), nullable=True),  # 'minor', 'major', 'pivotal'
        sa.Column('consequences', sa.Text(), nullable=True),

        # Metadata
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['universe_id'], ['universes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['elements.id'], ondelete='SET NULL')
    )
    op.create_index('idx_timeline_universe', 'timeline_events', ['universe_id'])
    op.create_index('idx_timeline_timestamp', 'timeline_events', ['event_timestamp'])
    op.create_index('idx_timeline_type', 'timeline_events', ['event_type'])

    # Add entity_subtype column to elements table
    op.add_column('elements', sa.Column('entity_subtype', sa.String(length=50), nullable=True))
    op.create_index('idx_elements_subtype', 'elements', ['entity_subtype'])

    # Note: CHECK constraints not added for SQLite compatibility
    # Validation will be enforced at the application level via Pydantic schemas


def downgrade() -> None:
    # Remove entity_subtype from elements
    op.drop_index('idx_elements_subtype', table_name='elements')
    op.drop_column('elements', 'entity_subtype')

    # Drop timeline_events table
    op.drop_index('idx_timeline_type', table_name='timeline_events')
    op.drop_index('idx_timeline_timestamp', table_name='timeline_events')
    op.drop_index('idx_timeline_universe', table_name='timeline_events')
    op.drop_table('timeline_events')

    # Drop entity_traits table
    op.drop_index('idx_entity_traits_key', table_name='entity_traits')
    op.drop_index('idx_entity_traits_element', table_name='entity_traits')
    op.drop_table('entity_traits')

    # Drop world_configs table
    op.drop_index('idx_world_configs_universe', table_name='world_configs')
    op.drop_table('world_configs')
