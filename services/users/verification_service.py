import logging
from random import randint
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException

from services.users.user_service import UserService
from services.users.email_service import send_email_task
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
        5. Send the code via email using Celery.
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

        # 5. Prepare email content
        subject = "Your Verification Code"
        body = f"Your verification code is: {code}\n\nThis code is valid for 10 minutes."
        html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Verify Your Email</title>
  <style>
    body {{
      font-family: Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      background-color: #f9f9f9;
      color: #333333;
    }}
    .container {{
      max-width: 600px;
      margin: 2rem auto;
      background-color: #ffffff;
      border-radius: 8px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      overflow: hidden;
    }}
    .header {{
      background-color: #4F6AFC;
      text-align: center;
      padding: 20px;
      color: #ffffff;
    }}
    .header .website {{
      font-size: 16px;
      margin-top: 10px;
      font-weight: bold;
    }}
    .content {{
      padding: 20px 30px;
      text-align: center;
    }}
    .content h1 {{
      color: #4F6AFC;
      font-size: 24px;
      margin-bottom: 16px;
    }}
    .content p {{
      margin: 0 0 16px;
      line-height: 1.6;
    }}
    .content .code {{
      font-size: 24px;
      font-weight: bold;
      color: #333333;
      padding: 10px 20px;
      background-color: #f4f4f4;
      border-radius: 4px;
      display: inline-block;
      margin: 20px 0;
    }}
    .footer {{
      text-align: center;
      padding: 10px;
      font-size: 12px;
      color: #888888;
      background-color: #f9f9f9;
      border-top: 1px solid #dddddd;
    }}
    .footer a {{
      color: #4F6AFC;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="website">
        <h1 style="color: #ffffff; font-size: 32px; font-weight: bold; margin: 0; letter-spacing: 3px; text-transform: uppercase;">
          <a href="https://speaknowly.com" style="color: #ffffff; text-decoration: none; display: block;">SPEAKNOWLY</a>
        </h1>
      </div>
    </div>
    <div class="content">
      <h1>{otp_type.name.replace('_', ' ').capitalize()}</h1>
      <p>Please use the following verification code. This code is valid for 10 minutes:</p>
      <p class="code">{code}</p>
      <p>If you did not request this code, you can safely ignore this email.</p>
      <p>Thank you,<br />The Speaknowly Team</p>
    </div>
    <div class="footer">
      &copy; {datetime.now().year} Speaknowly. All rights reserved.
    </div>
  </div>
</body>
</html>
"""

        # 6. Send email via Celery
        send_email_task.delay(subject, [email], body, html_body)

        # 7. Save or update the code in the database
        await VerificationCode.update_or_create(
            email=email,
            verification_type=otp_type,
            defaults={
                "code": int(code),
                "is_used": False,
                "is_expired": False,
                "created_at": datetime.now(timezone.utc),
            }
        )

        logger.info(f"Verification code sent to {email} for {verification_type}")
        return code

    @staticmethod
    async def verify_code(
        email: str,
        code: str,
        verification_type: str,
        user_id: int = None
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
        ).order_by("-updated_at").first()
        if not record:
            logger.info(f"Verification code not found or used for {email}")
            raise HTTPException(status_code=400, detail="Verification code not found or used")

        # 3. Check if the code is expired
        if datetime.now(timezone.utc) - record.updated_at > CODE_TTL:
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
        if otp_type == VerificationType.UPDATE_EMAIL and user_id:
            user = await UserService.get_by_id(user_id)
            if not user:
                logger.error(f"User not found for id: {user_id}")
                raise HTTPException(status_code=404, detail="User not found")
            logger.info(f"Verification code confirmed for user_id={user_id} (UPDATE_EMAIL)")
            return user
        else:
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
