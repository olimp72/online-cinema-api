import re
from pydantic import BaseModel, EmailStr, field_validator


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8 or not re.search(r"\d", value):
            raise ValueError("Password must be at least 8 characters long and contain a number")
        return value


class UserGroupUpdate(BaseModel):
    group_name: str
