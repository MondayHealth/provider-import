"""add unique constraints to all join tables

Revision ID: 8c2a2e49ee16
Revises: 922b9748f17e
Create Date: 2017-12-29 15:25:52.265723

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c2a2e49ee16'
down_revision = '922b9748f17e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'phones_addresses', ['phone_id', 'address_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_addresses', ['provider_id', 'address_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_credentials', ['provider_id', 'credential_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_groups', ['provider_id', 'group_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_languages', ['provider_id', 'language_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_modalities', ['provider_id', 'modality_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_orientations', ['provider_id', 'orientation_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_payment_methods', ['provider_id', 'payment_method_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_payors', ['provider_id', 'payor_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_phones', ['provider_id', 'phone_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_plans', ['provider_id', 'plan_id'], schema='monday')
    op.create_unique_constraint(None, 'providers_specialties', ['provider_id', 'specialty_id'], schema='monday')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'providers_specialties', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_plans', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_phones', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_payors', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_payment_methods', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_orientations', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_modalities', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_languages', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_groups', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_credentials', schema='monday', type_='unique')
    op.drop_constraint(None, 'providers_addresses', schema='monday', type_='unique')
    op.drop_constraint(None, 'phones_addresses', schema='monday', type_='unique')
    # ### end Alembic commands ###