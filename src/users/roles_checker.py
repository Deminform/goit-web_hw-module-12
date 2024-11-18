from fastapi.params import Depends
from fastapi import status, HTTPException, Request

from src.services.auth.jwt_auth import auth_service
from src.users.models import User
from src.users.schemas import RoleEnum


class RoleChecker:
    def __init__(self, allowed_roles: list[RoleEnum]):
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request, user: User = Depends(auth_service.get_current_user)):
        if user.role is None or user.role.name not in [role.value for role in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
