"""rename field

Revision ID: 21c6b8ab38fa
Revises: 8918a8f1d3b9
Create Date: 2017-12-30 21:42:17.424634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21c6b8ab38fa'
down_revision = '8918a8f1d3b9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('credential', sa.Column('full_name', sa.String(length=64), nullable=False), schema='monday')
    op.drop_constraint('credential_name_key', 'credential', schema='monday', type_='unique')
    op.create_unique_constraint(None, 'credential', ['full_name'], schema='monday')
    op.drop_column('credential', 'name', schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('credential', sa.Column('name', sa.VARCHAR(length=64), autoincrement=False, nullable=False), schema='monday')
    op.drop_constraint(None, 'credential', schema='monday', type_='unique')
    op.create_unique_constraint('credential_name_key', 'credential', ['name'], schema='monday')
    op.drop_column('credential', 'full_name', schema='monday')
    # ### end Alembic commands ###