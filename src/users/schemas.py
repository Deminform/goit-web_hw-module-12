import enum

from pydantic import BaseModel, Field, ConfigDict


class RoleEnum(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    GUEST = "guest"


class UserSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    password: str = Field(min_length=6, max_length=8)


class UserResponseSchema(BaseModel):
    id: int = 1
    username: str
    email: str
    avatar: str

    model_config = ConfigDict(from_attributes=True)


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmailSchema(BaseModel):
    email: str


class ResetPasswordSchema(BaseModel):
    password: str = Field(min_length=6, max_length=8)
    password_check: str = Field(min_length=6, max_length=8, description='Repeat password')
    temp_code: str = Field(pattern=r'^\d{6}$', description='Temporary code')
