"""Add social ids and phone to user

Revision ID: a6e891676abc
Revises: 580aab983719
Create Date: 2026-02-19 22:25:55.376144

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'a6e891676abc'
down_revision = '580aab983719'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    
    # Check for 'user' or renamed 'users'
    table_name = 'user' if 'user' in inspector.get_table_names() else 'users'
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        if 'phone_number' not in columns:
            batch_op.add_column(sa.Column('phone_number', sa.String(length=20), nullable=True))
        if 'google_id' not in columns:
            batch_op.add_column(sa.Column('google_id', sa.String(length=100), nullable=True))
        if 'apple_id' not in columns:
            batch_op.add_column(sa.Column('apple_id', sa.String(length=100), nullable=True))
        
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
        batch_op.alter_column('password_hash',
               existing_type=sa.VARCHAR(length=200),
               nullable=True)
        
        # Unique constraints
        fks_and_constraints = [c['name'] for c in inspector.get_unique_constraints(table_name)]
        if 'uq_user_apple_id' not in fks_and_constraints:
            batch_op.create_unique_constraint('uq_user_apple_id', ['apple_id'])
        if 'uq_user_google_id' not in fks_and_constraints:
            batch_op.create_unique_constraint('uq_user_google_id', ['google_id'])
        if 'uq_user_phone_number' not in fks_and_constraints:
            batch_op.create_unique_constraint('uq_user_phone_number', ['phone_number'])


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_apple_id', type_='unique')
        batch_op.drop_constraint('uq_user_google_id', type_='unique')
        batch_op.drop_constraint('uq_user_phone_number', type_='unique')
        batch_op.alter_column('password_hash',
               existing_type=sa.VARCHAR(length=200),
               nullable=False)
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
        batch_op.drop_column('apple_id')
        batch_op.drop_column('google_id')
        batch_op.drop_column('phone_number')
