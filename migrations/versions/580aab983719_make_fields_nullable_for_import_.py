"""make fields nullable for import resiliency

Revision ID: 580aab983719
Revises: fa4db74fead6
Create Date: 2026-02-18 11:06:40.983947

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '580aab983719'
down_revision = 'fa4db74fead6'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    
    # Safe alter_columns for Inventory
    if 'inventory' in inspector.get_table_names():
        with op.batch_alter_table('inventory', schema=None) as batch_op:
            batch_op.alter_column('product_id',
                   existing_type=sa.INTEGER(),
                   nullable=True)
            batch_op.alter_column('branch_id',
                   existing_type=sa.INTEGER(),
                   nullable=True)
            batch_op.alter_column('quantity_on_hand',
                   existing_type=sa.FLOAT(),
                   nullable=True)

    # Safe alter_columns for Product
    if 'product' in inspector.get_table_names():
        with op.batch_alter_table('product', schema=None) as batch_op:
            batch_op.alter_column('name',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=True)


def downgrade():
    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)

    with op.batch_alter_table('inventory', schema=None) as batch_op:
        batch_op.alter_column('quantity_on_hand',
               existing_type=sa.FLOAT(),
               nullable=False)
        batch_op.alter_column('branch_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('product_id',
               existing_type=sa.INTEGER(),
               nullable=False)
