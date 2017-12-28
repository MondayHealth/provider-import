"""index on licenses for uniqueness

Revision ID: 78d708f62754
Revises: eda96eabf504
Create Date: 2017-12-28 13:49:35.779505

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78d708f62754'
down_revision = 'eda96eabf504'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_monday_license_number_licensor_id_licensee_id', 'license', ['number', 'licensor_id', 'licensee_id'], unique=True, schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_monday_license_number_licensor_id_licensee_id', table_name='license', schema='monday')
    # ### end Alembic commands ###