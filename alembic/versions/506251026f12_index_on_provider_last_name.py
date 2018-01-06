"""index on provider last name

Revision ID: 506251026f12
Revises: cb06739ca641
Create Date: 2018-01-06 16:07:54.745073

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '506251026f12'
down_revision = 'cb06739ca641'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_monday_provider_last_name'), 'provider', ['last_name'], unique=False, schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_monday_provider_last_name'), table_name='provider', schema='monday')
    # ### end Alembic commands ###
