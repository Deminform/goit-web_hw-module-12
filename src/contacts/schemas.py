from datetime import date, datetime

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class ContactSchema(BaseModel):
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr = Field(..., max_length=50)
    phone: str = Field(max_length=10)
    birthday: date = Field(...)
    description: str = Field(None, max_length=300)


class ContactResponseSchema(ContactSchema):
    id: int
    created_at: datetime | None
    updated_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class ContactCreateSchema(ContactSchema):
    pass


class ContactUpdateSchema(ContactSchema):
    first_name: str = Field(None, min_length=2, max_length=100)
    last_name: str = Field(None)
    email: EmailStr = Field(None, max_length=50)
    phone: str = Field(None, max_length=10)
    birthday: date = Field(None)
    description: str = Field(None, max_length=300)
