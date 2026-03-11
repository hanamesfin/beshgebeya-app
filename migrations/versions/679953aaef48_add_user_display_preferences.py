"""add user display preferences

Revision ID: 679953aaef48
Revises: a6e891676abc
Create Date: 2026-02-22 22:17:42.165633

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '679953aaef48'
down_revision = 'a6e891676abc'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    
    table_name = 'user' if 'user' in inspector.get_table_names() else 'users'
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        if 'chart_style' not in columns:
            batch_op.add_column(sa.Column('chart_style', sa.String(length=20), nullable=True))
        if 'landing_page' not in columns:
            batch_op.add_column(sa.Column('landing_page', sa.String(length=20), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('landing_page')
        batch_op.drop_column('chart_style')
