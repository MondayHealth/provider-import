"""add email to provider

Revision ID: f8578b984cd0
Revises: 0eb4181b6d48
Create Date: 2018-02-06 16:58:36.136049

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f8578b984cd0'
down_revision = '0eb4181b6d48'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('provider', sa.Column('email', sa.String(length=512), nullable=True), schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('provider', 'email', schema='monday')
    # ### end Alembic commands ###
