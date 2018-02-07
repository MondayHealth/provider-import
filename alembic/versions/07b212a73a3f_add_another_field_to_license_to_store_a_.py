"""add another field to license to store a little more info

Revision ID: 07b212a73a3f
Revises: f8578b984cd0
Create Date: 2018-02-06 18:26:03.757972

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '07b212a73a3f'
down_revision = 'f8578b984cd0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('license', sa.Column('secondary_number', sa.String(length=8), nullable=True), schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('license', 'secondary_number', schema='monday')
    # ### end Alembic commands ###
