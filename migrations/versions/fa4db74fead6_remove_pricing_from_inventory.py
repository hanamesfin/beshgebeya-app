"""Remove pricing from inventory

Revision ID: fa4db74fead6
Revises: c5fb274d8f97
Create Date: 2026-02-18 00:16:32.098147

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'fa4db74fead6'
down_revision = 'c5fb274d8f97'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    columns = [c['name'] for c in inspector.get_columns('inventory')]

    with op.batch_alter_table('inventory', schema=None) as batch_op:
        if 'selling_price' in columns:
            batch_op.drop_column('selling_price')
        if 'cost_price' in columns:
            batch_op.drop_column('cost_price')


def downgrade():
    with op.batch_alter_table('inventory', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cost_price', sa.FLOAT(), nullable=True))
        batch_op.add_column(sa.Column('selling_price', sa.FLOAT(), nullable=True))
