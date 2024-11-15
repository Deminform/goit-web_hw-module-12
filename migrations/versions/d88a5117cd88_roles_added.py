"""Roles added

Revision ID: d88a5117cd88
Revises: d5e83aa1fe73
Create Date: 2024-11-16 00:06:47.415606

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.users.models import Role
from src.users.schemas import RoleEnum

# revision identifiers, used by Alembic.
revision: str = 'd88a5117cd88'
down_revision: Union[str, None] = 'd5e83aa1fe73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('users', sa.Column('role_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'users', 'roles', ['role_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'role_id')
    op.drop_table('roles')
    # ### end Alembic commands ###
