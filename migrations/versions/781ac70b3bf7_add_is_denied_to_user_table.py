"""Add is_denied to User table

Revision ID: 781ac70b3bf7
Revises: 305913cbcbe0
Create Date: 2026-03-04 12:48:36.321081

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '781ac70b3bf7'
down_revision = '305913cbcbe0'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    
    # --- sale_item alterations ---
    columns_sale_item = [c['name'] for c in inspector.get_columns('sale_item')]
    fks_sale_item = [fk['name'] for fk in inspector.get_foreign_keys('sale_item')]
    
    with op.batch_alter_table('sale_item', schema=None) as batch_op:
        if 'sale_id' not in columns_sale_item:
            batch_op.add_column(sa.Column('sale_id', sa.Integer(), nullable=True))
        if 'fk_sale_item_sale_id' not in fks_sale_item:
            try:
                batch_op.create_foreign_key('fk_sale_item_sale_id', 'sale', ['sale_id'], ['id'])
            except Exception:
                pass

    # --- user/users alterations ---
    table_name = 'user' if 'user' in inspector.get_table_names() else 'users'
    columns_user = [c['name'] for c in inspector.get_columns(table_name)]
    
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        if 'is_denied' not in columns_user:
            batch_op.add_column(sa.Column('is_denied', sa.Boolean(), server_default='0', nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('is_denied')

    with op.batch_alter_table('sale_item', schema=None) as batch_op:
        batch_op.drop_constraint('fk_sale_item_sale_id', type_='foreignkey')
        batch_op.drop_column('sale_id')
