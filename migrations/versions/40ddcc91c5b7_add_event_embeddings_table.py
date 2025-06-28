"""add_event_embeddings_table

Revision ID: 40ddcc91c5b7
Revises: 3ca0e38a88ec
Create Date: 2025-06-28 01:51:35.434570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40ddcc91c5b7'
down_revision: Union[str, None] = '3ca0e38a88ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём таблицу для векторных эмбеддингов событий
    op.create_table(
        'event_embeddings',
        sa.Column('event_id', sa.BigInteger(), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=True),  # Сохраняем как JSON строку
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('event_id')
    )
    
    # Создаём индекс для быстрого поиска по содержимому
    op.create_index('ix_event_embeddings_content', 'event_embeddings', ['content'])


def downgrade() -> None:
    op.drop_index('ix_event_embeddings_content', table_name='event_embeddings')
    op.drop_table('event_embeddings')
