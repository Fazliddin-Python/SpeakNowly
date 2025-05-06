from pydantic import BaseModel, EmailStr, Field, validator


class RegisterSerializer(BaseModel):
    """Serializer for user registration."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")

    @validator("password")
    def validate_password(cls, value):
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter")
        return value


class RegisterResponseSerializer(BaseModel):
    """Serializer for registration response."""
    message: str = Field(..., description="Response message")