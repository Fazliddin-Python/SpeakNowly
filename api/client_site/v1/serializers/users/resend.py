from pydantic import BaseModel, EmailStr, Field

class ResendSerializer(BaseModel):
    email: EmailStr = Field(..., description="Email to resend the verification code")
    type: str = Field(..., description="Type of verification (e.g., REGISTER, FORGET_PASSWORD, UPDATE_EMAIL)")