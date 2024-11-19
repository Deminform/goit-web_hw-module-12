import enum

from pydantic import BaseModel, Field, EmailStr


class RoleEnum(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    GUEST = "guest"


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponseSchema(BaseModel):
    id: int = 1
    username: str
    email: str
    avatar: str

    class Config:
        from_attributes = True


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr
