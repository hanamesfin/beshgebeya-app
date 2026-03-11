"""Add user approval and reset fields

Revision ID: 305913cbcbe0
Revises: 679953aaef48
Create Date: 2026-02-27 12:01:30.345581

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '305913cbcbe0'
down_revision = '679953aaef48'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    
    table_name = 'user' if 'user' in inspector.get_table_names() else 'users'
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    constraints = [c['name'] for c in inspector.get_unique_constraints(table_name)]
    
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        if 'is_approved' not in columns:
            batch_op.add_column(sa.Column('is_approved', sa.Boolean(), nullable=True))
        if 'reset_token' not in columns:
            batch_op.add_column(sa.Column('reset_token', sa.String(length=100), nullable=True))
        if 'reset_token_expiry' not in columns:
            batch_op.add_column(sa.Column('reset_token_expiry', sa.DateTime(), nullable=True))
            
        if 'uq_user_reset_token' not in constraints:
            batch_op.create_unique_constraint('uq_user_reset_token', ['reset_token'])


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_reset_token', type_='unique')
        batch_op.drop_column('reset_token_expiry')
        batch_op.drop_column('reset_token')
        batch_op.drop_column('is_approved')
