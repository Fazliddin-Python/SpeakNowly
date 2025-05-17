import logging
from random import randint
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from services.users.email_service import EmailService
from services.users.user_service import UserService
from models.users.verification_codes import VerificationCode, VerificationType
from models.users.users import User

CODE_TTL = timedelta(minutes=10)
logger = logging.getLogger("verification_service")

class VerificationService:
    """
    Service for handling email verification during registration and other flows.
    """

    @staticmethod
    async def send_verification_code(email: str, verification_type: str) -> str:
        """
        1. Validate verification type.
        2. Check resend limiter (block if too frequent).
        3. Check if user is already verified (for registration).
        4. Generate a random verification code.
        5. Send the code via email using EmailService.
        6. Save or update the code in the database.
        7. Return the code.
        """
        try:
            otp_type = VerificationType(verification_type)
        except ValueError:
            logger.warning(f"Invalid verification type: {verification_type}")
            raise HTTPException(status_code=400, detail="Invalid verification type")

        # 2. Check resend limiter
        if hasattr(VerificationCode, "is_resend_blocked"):
            if await VerificationCode.is_resend_blocked(email, otp_type):
                logger.info(f"Resend blocked for {email} ({otp_type})")
                raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
        else:
            logger.error("is_resend_blocked method not implemented in VerificationCode")
            raise HTTPException(status_code=500, detail="Internal server error")

        # 3. Check if user is already verified (for registration)
        user = await UserService.get_by_email(email)
        if user and user.is_verified and otp_type == VerificationType.REGISTER:
            logger.info(f"Attempt to register already verified email: {email}")
            raise HTTPException(status_code=400, detail="Email already registered")

        # 4. Generate a random code
        code = f"{randint(10000, 99999)}"

        # 5. Send the code via email
        await EmailService.send_email(
            subject="Your Verification Code",
            recipients=[email],
            verification_type=verification_type,
            code=code
        )

        # 6. Save or update the code in the database
        await VerificationCode.create(
            email=email,
            verification_type=otp_type,
            code=int(code),
            is_used=False,
            is_expired=False
        )

        # 7. Optionally: delete old unused codes to keep DB clean
        await VerificationCode.filter(
            email=email,
            verification_type=otp_type,
            is_used=False,
            is_expired=False
        ).exclude(code=int(code)).delete()

        logger.info(f"Verification code sent to {email} for {verification_type}")
        return code

    @staticmethod
    async def verify_code(
        email: str,
        code: str,
        verification_type: str
    ) -> User:
        """
        1. Validate verification type.
        2. Retrieve the latest unused, unexpired code for the user.
        3. Check if the code exists and is valid.
        4. Check if the code is expired.
        5. Check if the code matches.
        6. Mark the code as used.
        7. Return the user.
        """
        # 1. Validate verification type
        try:
            otp_type = VerificationType(verification_type)
        except ValueError:
            logger.warning(f"Invalid verification type: {verification_type}")
            raise HTTPException(status_code=400, detail="Invalid verification type")

        # 2. Retrieve the latest unused, unexpired code
        record = await VerificationCode.filter(
            email=email,
            verification_type=otp_type,
            is_used=False,
            is_expired=False
        ).order_by("-created_at").first()
        if not record:
            logger.info(f"Verification code not found or used for {email}")
            raise HTTPException(status_code=400, detail="Verification code not found or used")

        # 3. Check if the code is expired
        if datetime.now(timezone.utc) - record.created_at > CODE_TTL:
            record.is_expired = True
            await record.save()
            logger.info(f"Verification code expired for {email}")
            raise HTTPException(status_code=400, detail="Verification code expired")

        # 4. Check if the code matches
        if str(record.code) != str(code):
            logger.info(f"Invalid verification code for {email}")
            raise HTTPException(status_code=400, detail="Invalid verification code")

        # 5. Mark the code as used
        record.is_used = True
        await record.save()

        # 6. Return the user
        user = await UserService.get_by_email(email)
        if not user:
            logger.error(f"User not found for email: {email}")
            raise HTTPException(status_code=404, detail="User not found")
        logger.info(f"Verification code confirmed for {email}")
        return user

    @staticmethod
    async def delete_unused_codes(email: str, verification_type: str) -> None:
        """
        1. Validate verification type.
        2. Delete all unused and unexpired codes for the user.
        """
        try:
            otp_type = VerificationType(verification_type)
        except ValueError:
            logger.warning(f"Invalid verification type: {verification_type}")
            raise HTTPException(status_code=400, detail="Invalid verification type")

        await VerificationCode.filter(
            email=email,
            verification_type=otp_type,
            is_used=False,
            is_expired=False
        ).delete()
        logger.info(f"Unused verification codes deleted for {email} ({verification_type})")
