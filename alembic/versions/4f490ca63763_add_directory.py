"""add directory

Revision ID: 4f490ca63763
Revises: a8f88ff8ed2a
Create Date: 2017-12-21 15:38:53.833991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4f490ca63763'
down_revision = 'a8f88ff8ed2a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('directory',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('short_name', sa.String(length=32), nullable=False),
    sa.Column('record_limit', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='monday'
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('directory', schema='monday')
    # ### end Alembic commands ###
