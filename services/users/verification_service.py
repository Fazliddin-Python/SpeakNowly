from random import randint
from fastapi import HTTPException

from services.users.email_service import EmailService
from services.users.user_service import UserService


class VerificationService:
    """
    Service handling email verification during registration.
    """

    @staticmethod
    async def send_verification_code(email: str, verification_type: str) -> str:
        """
        Generate and send a verification code to user email.
        Returns the code for temporary storage.
        """
        user = await UserService.get_by_email(email)
        if user and user.is_verified:
            raise HTTPException(status_code=400, detail="Email already registered")

        code = f"{randint(100000, 999999)}"
        await EmailService.send_email(
            subject="Your Verification Code",
            recipients=[email],
            verification_type=verification_type,
            code=code
        )
        return code

    @staticmethod
    async def verify_code(
        email: str,
        code: str,
        expected_code: str
    ) -> bool:
        """
        Validate the provided code against the expected one.
        """
        if code != expected_code:
            raise HTTPException(status_code=400, detail="Invalid verification code")
        return True