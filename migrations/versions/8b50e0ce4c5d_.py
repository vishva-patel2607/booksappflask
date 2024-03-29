"""empty message

Revision ID: 8b50e0ce4c5d
Revises: 163514ebf0fc
Create Date: 2022-02-10 15:11:45.490862

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8b50e0ce4c5d'
down_revision = '163514ebf0fc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('booksapp_userpntoken', sa.Column('platform', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('booksapp_userpntoken', 'platform')
    
    # ### end Alembic commands ###
