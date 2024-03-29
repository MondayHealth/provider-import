"""provider directory relationship

Revision ID: a6bcffae1e43
Revises: 19e625982be8
Create Date: 2018-02-04 12:52:15.060571

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a6bcffae1e43'
down_revision = '19e625982be8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('providers_directories',
    sa.Column('provider_id', sa.Integer(), nullable=True),
    sa.Column('directory_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['directory_id'], ['monday.directory.id'], ),
    sa.ForeignKeyConstraint(['provider_id'], ['monday.provider.id'], ),
    sa.UniqueConstraint('provider_id', 'directory_id'),
    schema='monday'
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('providers_directories', schema='monday')
    # ### end Alembic commands ###
