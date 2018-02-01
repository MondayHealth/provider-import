"""add mark for gt/pt phone

Revision ID: a9adfd3c2eba
Revises: 4a099379fe64
Create Date: 2018-01-31 23:38:04.395436

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a9adfd3c2eba'
down_revision = '4a099379fe64'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('phone', sa.Column('directory', sa.Integer(), nullable=True), schema='monday')
    op.drop_column('phone', 'psych_today', schema='monday')
    op.drop_column('phone', 'good_therapy', schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('phone', sa.Column('good_therapy', sa.BOOLEAN(), autoincrement=False, nullable=True), schema='monday')
    op.add_column('phone', sa.Column('psych_today', sa.BOOLEAN(), autoincrement=False, nullable=True), schema='monday')
    op.drop_column('phone', 'directory', schema='monday')
    # ### end Alembic commands ###
