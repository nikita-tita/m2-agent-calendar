"""Add notification fields

Revision ID: add_notification_fields
Revises: 3ca0e38a88ec
Create Date: 2024-12-19 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'add_notification_fields'
down_revision = '3ca0e38a88ec'
branch_labels = None
depends_on = None

def upgrade():
    # Добавляем поля в таблицу events
    op.add_column('events', sa.Column('is_reminder_sent', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('idx_events_is_reminder_sent', 'events', ['is_reminder_sent'])
    
    # Добавляем поля в таблицу users
    op.add_column('users', sa.Column('reminder_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('daily_digest_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('users', sa.Column('preferences', sa.JSON(), nullable=False, server_default='{}'))

def downgrade():
    # Удаляем поля из таблицы events
    op.drop_index('idx_events_is_reminder_sent', 'events')
    op.drop_column('events', 'is_reminder_sent')
    
    # Удаляем поля из таблицы users
    op.drop_column('users', 'reminder_enabled')
    op.drop_column('users', 'daily_digest_enabled')
    op.drop_column('users', 'preferences') 