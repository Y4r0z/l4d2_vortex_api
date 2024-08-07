"""added nickname in chat logs

Revision ID: b2004e3c7555
Revises: 35c7d4dd0cd1
Create Date: 2024-07-27 22:31:02.245466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2004e3c7555'
down_revision: Union[str, None] = '35c7d4dd0cd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('chatLogs', sa.Column('nickname', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('chatLogs', 'nickname')
    # ### end Alembic commands ###
