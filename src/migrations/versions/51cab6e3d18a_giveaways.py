"""giveaways

Revision ID: 51cab6e3d18a
Revises: 8b880f30f8e7
Create Date: 2024-08-06 21:19:30.724288

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '51cab6e3d18a'
down_revision: Union[str, None] = '8b880f30f8e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('giveaway',
    sa.Column('userId', sa.Integer(), nullable=False),
    sa.Column('timeCreated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('activeUntil', sa.DateTime(timezone=True), nullable=False),
    sa.Column('maxUseCount', sa.Integer(), nullable=False),
    sa.Column('curUseCount', sa.Integer(), nullable=False),
    sa.Column('reward', sa.Integer(), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['userId'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('giveawayUse',
    sa.Column('userId', sa.Integer(), nullable=False),
    sa.Column('giveawayId', sa.Integer(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['giveawayId'], ['giveaway.id'], ),
    sa.ForeignKeyConstraint(['userId'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('giveawayUse')
    op.drop_table('giveaway')
    # ### end Alembic commands ###
