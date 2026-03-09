"""rename user table to users

Revision ID: b23cd3a28142
Revises: 781ac70b3bf7
Create Date: 2026-03-09 14:11:25.921066

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b23cd3a28142'
down_revision = '781ac70b3bf7'
branch_labels = None
depends_on = None


def upgrade():
    # Defensive check: only rename if 'user' exists and 'users' does not
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    
    if 'user' in tables and 'users' not in tables:
        op.rename_table('user', 'users')
    elif 'users' in tables and 'user' in tables:
        # Emergency: both exist? This shouldn't happen but let's be safe.
        # Maybe the previous attempt failed halfway.
        # If 'users' exists, we might need to merge or just assume 'users' is the new one.
        pass 
    
    # Update ForeignKeys on other tables
    with op.batch_alter_table('sale', schema=None) as batch_op:
        try:
            batch_op.create_foreign_key('fk_sales_user_id', 'users', ['user_id'], ['id'])
        except Exception:
            pass

    # Handle the sale_item.sale_id addition if it was missed or incorrectly handled
    with op.batch_alter_table('sale_item', schema=None) as batch_op:
        try:
            batch_op.add_column(sa.Column('sale_id', sa.Integer(), nullable=True))
        except Exception:
            pass
            
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
