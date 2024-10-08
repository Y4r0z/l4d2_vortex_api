"""added server statistics

Revision ID: 6fda241be9b9
Revises: 407d5aaa2382
Create Date: 2024-08-20 18:33:23.121690

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6fda241be9b9'
down_revision: Union[str, None] = '407d5aaa2382'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('serverStats',
    sa.Column('time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('players', sa.Integer(), nullable=False),
    sa.Column('maxPlayers', sa.Integer(), nullable=False),
    sa.Column('map', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('ping', sa.Integer(), nullable=False),
    sa.Column('ip', sa.String(length=32), nullable=False),
    sa.Column('port', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('serverStats')
    # ### end Alembic commands ###
