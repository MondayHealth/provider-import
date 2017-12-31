"""increase length of cert name

Revision ID: ccdd03b4704a
Revises: 21c6b8ab38fa
Create Date: 2017-12-31 14:07:21.059916

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ccdd03b4704a'
down_revision = '21c6b8ab38fa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('credential', 'full_name',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=128),
               existing_nullable=False,
               schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('credential', 'full_name',
               existing_type=sa.String(length=128),
               type_=sa.VARCHAR(length=64),
               existing_nullable=False,
               schema='monday')
    # ### end Alembic commands ###
