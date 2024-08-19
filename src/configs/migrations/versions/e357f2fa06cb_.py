"""empty message

Revision ID: e357f2fa06cb
Revises: 
Create Date: 2024-07-30 10:29:30.557102

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e357f2fa06cb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('logs',
    sa.Column('identifier', sa.String(), nullable=False),
    sa.Column('ias', sa.JSON(), nullable=False),
    sa.Column('product', sa.String(), nullable=False),
    sa.Column('plate', sa.String(), nullable=False),
    sa.Column('angle', sa.String(), nullable=True),
    sa.Column('result', sa.JSON(), nullable=True),
    sa.Column('runtime', sa.Float(), nullable=True),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('logs')
    # ### end Alembic commands ###
