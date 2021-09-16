"""empty message

Revision ID: d07eb1d4765d
Revises: 7b9ff99b8c79
Create Date: 2021-09-16 18:37:38.189991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd07eb1d4765d'
down_revision = '7b9ff99b8c79'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    #op.drop_table('spatial_ref_sys')
    op.add_column('booksapp_store', sa.Column('usernumber', sa.BigInteger(), nullable=False))
    op.add_column('booksapp_store', sa.Column('store_latitude', sa.Float(), nullable=False))
    op.add_column('booksapp_store', sa.Column('store_longitude', sa.Float(), nullable=False))
    #op.drop_index('idx_booksapp_store_store_location', table_name='booksapp_store')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('idx_booksapp_store_store_location', 'booksapp_store', ['store_location'], unique=False)
    op.drop_column('booksapp_store', 'store_longitude')
    op.drop_column('booksapp_store', 'store_latitude')
    op.drop_column('booksapp_store', 'usernumber')
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