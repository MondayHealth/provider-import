"""add unique index for modalities

Revision ID: 3cccf6a0af7d
Revises: ba3bae2b5e27
Create Date: 2018-01-05 14:28:03.194013

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3cccf6a0af7d'
down_revision = 'ba3bae2b5e27'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_monday_modality_name'), 'modality', ['name'], unique=True, schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_monday_modality_name'), table_name='modality', schema='monday')
    # ### end Alembic commands ###
