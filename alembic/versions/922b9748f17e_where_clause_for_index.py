"""where clause for index

Revision ID: 922b9748f17e
Revises: 78d708f62754
Create Date: 2017-12-29 11:53:00.889623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '922b9748f17e'
down_revision = '78d708f62754'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_monday_phone_npa_nxx_xxxx_null', 'phone', ['npa', 'nxx', 'xxxx'], unique=True, schema='monday', postgresql_where=sa.text('extension IS NULL'))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_monday_phone_npa_nxx_xxxx_null', table_name='phone', schema='monday')
    # ### end Alembic commands ###
