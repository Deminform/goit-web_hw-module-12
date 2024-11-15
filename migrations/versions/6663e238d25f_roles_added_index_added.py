"""Roles added, Index added

Revision ID: 6663e238d25f
Revises: d88a5117cd88
Create Date: 2024-11-16 01:31:01.647868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.users.models import Role
from src.users.schemas import RoleEnum

# revision identifiers, used by Alembic.
revision: str = '6663e238d25f'
down_revision: Union[str, None] = 'd88a5117cd88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.drop_column('roles', 'description')
    op.drop_constraint('users_email_key', 'users', type_='unique')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    # ### end Alembic commands ###

    op.bulk_insert(
        Role.__table__,
        [
            {'id': 1, 'name': RoleEnum.GUEST.value},
            {'id': 2, 'name': RoleEnum.USER.value},
            {'id': 3, 'name': RoleEnum.ADMIN.value},
        ]
    )


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_unique_constraint('users_email_key', 'users', ['email'])
    op.add_column('roles', sa.Column('description', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    # ### end Alembic commands ###
