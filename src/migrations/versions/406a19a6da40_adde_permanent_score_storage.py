"""Adde permanent score storage

Revision ID: 406a19a6da40
Revises: 5279727ad1fa
Create Date: 2024-07-29 20:44:59.090097

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '406a19a6da40'
down_revision: Union[str, None] = '5279727ad1fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('roundScore_Permanent',
    sa.Column('userId', sa.Integer(), nullable=False),
    sa.Column('agression', sa.Integer(), nullable=False),
    sa.Column('support', sa.Integer(), nullable=False),
    sa.Column('perks', sa.Integer(), nullable=False),
    sa.Column('team', sa.SmallInteger(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['userId'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('roundScore_Permanent')
    # ### end Alembic commands ###
