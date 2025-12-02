"""update_schema_for_comprehensive_listing_data

Revision ID: f45a2841c8ac
Revises: db93b7db6129
Create Date: 2025-12-01 10:30:19.676573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f45a2841c8ac'
down_revision: Union[str, Sequence[str], None] = 'db93b7db6129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns
    op.add_column('listings', sa.Column('auction_type', sa.String(), nullable=True))
    op.add_column('listings', sa.Column('guarantee_amount', sa.String(), nullable=True))
    op.add_column('listings', sa.Column('bid_count', sa.Integer(), nullable=True))
    op.add_column('listings', sa.Column('viewing_deadline', sa.DateTime(), nullable=True))
    op.add_column('listings', sa.Column('scrape_errors', sa.Text(), nullable=True))
    op.add_column('listings', sa.Column('is_active', sa.Boolean(), nullable=True))
    op.add_column('listings', sa.Column('is_sold', sa.Boolean(), nullable=True))
    
    # Create indexes for new boolean columns
    op.create_index(op.f('ix_listings_is_active'), 'listings', ['is_active'], unique=False)
    op.create_index(op.f('ix_listings_is_sold'), 'listings', ['is_sold'], unique=False)
    
    # Convert price columns from Float to String
    # SQLite doesn't support ALTER COLUMN, so we need to:
    # 1. Create new columns
    # 2. Copy data (converting float to string)
    # 3. Drop old columns
    # 4. Rename new columns
    
    # Add temporary columns
    op.add_column('listings', sa.Column('starting_price_new', sa.String(), nullable=True))
    op.add_column('listings', sa.Column('current_offer_new', sa.String(), nullable=True))
    
    # Copy and convert data
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE listings 
        SET starting_price_new = CAST(starting_price AS TEXT)
        WHERE starting_price IS NOT NULL
    """))
    connection.execute(sa.text("""
        UPDATE listings 
        SET current_offer_new = CAST(current_offer AS TEXT)
        WHERE current_offer IS NOT NULL
    """))
    
    # Set default values for new boolean columns
    connection.execute(sa.text("""
        UPDATE listings 
        SET is_active = 1, is_sold = 0
        WHERE is_active IS NULL OR is_sold IS NULL
    """))
    
    # Drop old price columns
    op.drop_column('listings', 'starting_price')
    op.drop_column('listings', 'current_offer')
    
    # Rename new columns to original names
    # SQLite doesn't support RENAME COLUMN directly in all versions, so we recreate
    op.add_column('listings', sa.Column('starting_price', sa.String(), nullable=True))
    op.add_column('listings', sa.Column('current_offer', sa.String(), nullable=True))
    
    connection.execute(sa.text("""
        UPDATE listings 
        SET starting_price = starting_price_new,
            current_offer = current_offer_new
    """))
    
    op.drop_column('listings', 'starting_price_new')
    op.drop_column('listings', 'current_offer_new')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f('ix_listings_is_sold'), table_name='listings')
    op.drop_index(op.f('ix_listings_is_active'), table_name='listings')
    
    # Drop new columns
    op.drop_column('listings', 'is_sold')
    op.drop_column('listings', 'is_active')
    op.drop_column('listings', 'scrape_errors')
    op.drop_column('listings', 'viewing_deadline')
    op.drop_column('listings', 'bid_count')
    op.drop_column('listings', 'guarantee_amount')
    op.drop_column('listings', 'auction_type')
    
    # Convert price columns back to Float
    op.add_column('listings', sa.Column('starting_price_new', sa.Float(), nullable=True))
    op.add_column('listings', sa.Column('current_offer_new', sa.Float(), nullable=True))
    
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE listings 
        SET starting_price_new = CAST(starting_price AS REAL)
        WHERE starting_price IS NOT NULL
    """))
    connection.execute(sa.text("""
        UPDATE listings 
        SET current_offer_new = CAST(current_offer AS REAL)
        WHERE current_offer IS NOT NULL
    """))
    
    op.drop_column('listings', 'starting_price')
    op.drop_column('listings', 'current_offer')
    
    op.add_column('listings', sa.Column('starting_price', sa.Float(), nullable=True))
    op.add_column('listings', sa.Column('current_offer', sa.Float(), nullable=True))
    
    connection.execute(sa.text("""
        UPDATE listings 
        SET starting_price = starting_price_new,
            current_offer = current_offer_new
    """))
    
    op.drop_column('listings', 'starting_price_new')
    op.drop_column('listings', 'current_offer_new')
