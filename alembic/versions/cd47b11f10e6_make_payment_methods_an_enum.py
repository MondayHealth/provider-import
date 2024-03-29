"""make payment methods an enum

Revision ID: cd47b11f10e6
Revises: ccdd03b4704a
Create Date: 2018-01-02 15:23:19.059663

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cd47b11f10e6'
down_revision = 'ccdd03b4704a'
branch_labels = None
depends_on = None


def upgrade():
    e = sa.Enum('cash', 'check', 'wire', 'ach', 'hsa', 'amex', 'discover', 'mastercard', 'visa', 'paypal', 'venmo', 'apple', 'android', name='paymentmethodtype')
    e.create(op.get_bind(), checkfirst=True)

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('payment_method', sa.Column('payment_type', e, nullable=False), schema='monday')
    op.create_unique_constraint(None, 'payment_method', ['payment_type'], schema='monday')
    op.drop_column('payment_method', 'name', schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('payment_method', sa.Column('name', sa.VARCHAR(length=32), autoincrement=False, nullable=False), schema='monday')
    op.drop_constraint(None, 'payment_method', schema='monday', type_='unique')
    op.drop_column('payment_method', 'payment_type', schema='monday')
    # ### end Alembic commands ###
