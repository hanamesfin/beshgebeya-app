"""rename user table to users

Revision ID: b23cd3a28142
Revises: 781ac70b3bf7
Create Date: 2026-03-09 14:11:25.921066

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'b23cd3a28142'
down_revision = '781ac70b3bf7'
branch_labels = None
depends_on = None


def upgrade():
    # Defensive check: only rename if 'user' exists and 'users' does not
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    tables = inspector.get_table_names()
    
    if 'user' in tables and 'users' not in tables:
        op.rename_table('user', 'users')
    
    # Update ForeignKeys on 'sale' table
    fks_sale = [fk['name'] for fk in inspector.get_foreign_keys('sale')]
    if 'fk_sales_user_id' not in fks_sale:
        with op.batch_alter_table('sale', schema=None) as batch_op:
            try:
                batch_op.create_foreign_key('fk_sales_user_id', 'users', ['user_id'], ['id'])
            except Exception:
                pass

    # Handle the sale_id addition and foreign key safety check on 'sale_item'
    columns_sale_item = [c['name'] for c in inspector.get_columns('sale_item')]
    fks_sale_item = [fk['name'] for fk in inspector.get_foreign_keys('sale_item')]
    
    with op.batch_alter_table('sale_item', schema=None) as batch_op:
        if 'sale_id' not in columns_sale_item:
            batch_op.add_column(sa.Column('sale_id', sa.Integer(), nullable=True))
            
        # Ensure foreign key is set only if it doesn't exist
        if 'fk_sale_item_sale_id' not in fks_sale_item:
            try:
                batch_op.create_foreign_key('fk_sale_item_sale_id', 'sale', ['sale_id'], ['id'])
            except Exception:
                pass

def downgrade():
    with op.batch_alter_table('sale_item', schema=None) as batch_op:
        batch_op.drop_constraint('fk_sale_item_sale_id', type_='foreignkey')
        batch_op.drop_column('sale_id')

    with op.batch_alter_table('sale', schema=None) as batch_op:
        batch_op.drop_constraint('fk_sales_user_id', type_='foreignkey')
        batch_op.create_foreign_key('fk_sale_user_id', 'user', ['user_id'], ['id'])

    op.rename_table('users', 'user')
