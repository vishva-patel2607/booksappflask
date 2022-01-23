"""empty message

Revision ID: b8f4ab8a7c68
Revises: a628cc041c3c
Create Date: 2022-01-23 17:12:43.988776

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8f4ab8a7c68'
down_revision = 'a628cc041c3c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    #op.drop_table('spatial_ref_sys')
    #op.drop_index('idx_booksapp_store_store_location', table_name='booksapp_store')
    op.add_column('booksapp_transaction', sa.Column('borrower_price', sa.BigInteger(), nullable=True))
    op.add_column('booksapp_transaction', sa.Column('lender_cost', sa.BigInteger(), nullable=True))
    op.add_column('booksapp_transaction', sa.Column('store_cost', sa.BigInteger(), nullable=True))
    op.add_column('booksapp_transaction', sa.Column('company_cost', sa.BigInteger(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('booksapp_transaction', 'company_cost')
    op.drop_column('booksapp_transaction', 'store_cost')
    op.drop_column('booksapp_transaction', 'lender_cost')
    op.drop_column('booksapp_transaction', 'borrower_price')
    op.create_index('idx_booksapp_store_store_location', 'booksapp_store', ['store_location'], unique=False)
    op.create_table('spatial_ref_sys',
    sa.Column('srid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('auth_name', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    sa.Column('auth_srid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('srtext', sa.VARCHAR(length=2048), autoincrement=False, nullable=True),
    sa.Column('proj4text', sa.VARCHAR(length=2048), autoincrement=False, nullable=True),
    sa.CheckConstraint('(srid > 0) AND (srid <= 998999)', name='spatial_ref_sys_srid_check'),
    sa.PrimaryKeyConstraint('srid', name='spatial_ref_sys_pkey')
    )
    # ### end Alembic commands ###
