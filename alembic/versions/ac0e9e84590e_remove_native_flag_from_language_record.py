"""remove native flag from language record

Revision ID: ac0e9e84590e
Revises: caf530452432
Create Date: 2018-01-04 13:29:43.671970

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ac0e9e84590e'
down_revision = 'caf530452432'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('language', 'native', schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('language', sa.Column('native', sa.BOOLEAN(), autoincrement=False, nullable=True), schema='monday')
    # ### end Alembic commands ###
