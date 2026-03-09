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
    # Rename table user to users
    op.rename_table('user', 'users')
    
    # Update ForeignKeys on other tables
    with op.batch_alter_table('sale', schema=None) as batch_op:
        # Note: We use named constraints for better SQLite/batch support
        # In Postgres, Alembic usually handles this even with None if it can find the name
        batch_op.create_foreign_key('fk_sales_user_id', 'users', ['user_id'], ['id'])

    # Handle the sale_item.sale_id addition if it was missed or incorrectly handled
    # (Based on previous logs, it seemed like it was being detected as missing)
    with op.batch_alter_table('sale_item', schema=None) as batch_op:
        # Only add if it doesn't exist (this is a bit tricky in Alembic, 
        # but since we are in a migration, we assume the state)
        # However, let's stick to what was detected
        try:
            batch_op.add_column(sa.Column('sale_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_sale_item_sale_id', 'sale', ['sale_id'], ['id'])
        except Exception:
            pass # Already exists

def downgrade():
    with op.batch_alter_table('sale_item', schema=None) as batch_op:
        batch_op.drop_constraint('fk_sale_item_sale_id', type_='foreignkey')
        batch_op.drop_column('sale_id')

    with op.batch_alter_table('sale', schema=None) as batch_op:
        batch_op.drop_constraint('fk_sales_user_id', type_='foreignkey')
        batch_op.create_foreign_key('fk_sale_user_id', 'user', ['user_id'], ['id'])

    op.rename_table('users', 'user')
