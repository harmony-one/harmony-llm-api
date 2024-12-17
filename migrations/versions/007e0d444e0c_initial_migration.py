"""initial migration

Revision ID: 007e0d444e0c
Revises: 
Create Date: 2024-12-16 19:24:20.967005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007e0d444e0c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('collection_errors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('collection_name', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sign_in_requests',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('address', sa.String(length=42), nullable=False),
    sa.Column('nonce', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('address')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('address', sa.String(length=42), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('user_type', sa.Enum('WALLET', 'API_KEY', name='usertype'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('address'),
    sa.UniqueConstraint('username')
    )
    op.create_table('tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('jti', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('jti')
    )
    op.create_table('transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Enum('DEPOSIT', 'WITHDRAWAL', 'API_USAGE', 'REFUND', name='transactiontype'), nullable=False),
    sa.Column('amount', sa.Numeric(precision=18, scale=8), nullable=False),
    sa.Column('tx_hash', sa.String(length=66), nullable=True),
    sa.Column('model_type', sa.String(length=50), nullable=True),
    sa.Column('tokens_input', sa.Integer(), nullable=True),
    sa.Column('tokens_output', sa.Integer(), nullable=True),
    sa.Column('request_id', sa.String(length=36), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('endpoint', sa.String(length=100), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('transaction_metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('request_id'),
    sa.UniqueConstraint('tx_hash')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transactions')
    op.drop_table('tokens')
    op.drop_table('users')
    op.drop_table('sign_in_requests')
    op.drop_table('collection_errors')
    # ### end Alembic commands ###
