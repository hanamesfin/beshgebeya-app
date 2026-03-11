"""Add size and pack fields to Inventory

Revision ID: c5fb274d8f97
Revises: 2764984cda81
Create Date: 2026-02-17 22:40:38.310130

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'c5fb274d8f97'
down_revision = '2764984cda81'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    columns = [c['name'] for c in inspector.get_columns('inventory')]
    
    with op.batch_alter_table('inventory', schema=None) as batch_op:
        if 'unit_size' not in columns:
            batch_op.add_column(sa.Column('unit_size', sa.Float(), nullable=True))
        if 'unit_measure' not in columns:
            batch_op.add_column(sa.Column('unit_measure', sa.String(length=20), nullable=True))
        if 'pack_qty' not in columns:
            batch_op.add_column(sa.Column('pack_qty', sa.Integer(), nullable=True))
        if 'pack_unit' not in columns:
            batch_op.add_column(sa.Column('pack_unit', sa.String(length=20), nullable=True))
        if 'extra_info' not in columns:
            batch_op.add_column(sa.Column('extra_info', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('inventory', schema=None) as batch_op:
        batch_op.drop_column('extra_info')
        batch_op.drop_column('pack_unit')
        batch_op.drop_column('pack_qty')
        batch_op.drop_column('unit_measure')
        batch_op.drop_column('unit_size')
