import asyncio
from typing import Optional, Any
from fastapi import HTTPException, status, Request
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction
from passlib.hash import bcrypt
from pydantic import EmailStr, ValidationError
from pydantic import validate_email as pydantic_validate_email, ValidationError

from models.users.users import User
from models.tariffs import Tariff
from models.transactions import TokenTransaction, TransactionType

import logging

logger = logging.getLogger("user_service")

ALLOWED_UPDATE_FIELDS = {
    "email", "first_name", "last_name", "age", "photo", "last_login",
    "is_active", "is_verified"
}
ADMIN_ALLOWED_UPDATE_FIELDS = {
    "email", "first_name", "last_name", "age", "photo", "last_login",
    "is_active", "is_verified", "is_staff", "is_superuser"
}

from utils.i18n import _TRANSLATIONS

def get_translations_from_request(request: Request):
    lang = request.headers.get("Accept-Language", "en").split(",")[0]
    return _TRANSLATIONS.get(lang, _TRANSLATIONS["en"])

def validate_email(email: str, t: dict):
    try:
        pydantic_validate_email(email)
    except ValidationError:
        raise HTTPException(status_code=400, detail=t["invalid_email_format"])

def validate_password(password: str) -> None:
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password too short (min 8 chars)")
    if password.isdigit() or password.isalpha():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must contain letters and numbers")

class UserService:
    """
    Service layer for user operations: registration, authentication, profile update, password management.
    """

    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        """Retrieve a user by email."""
        try:
            return await User.get(email=email)
        except DoesNotExist:
            return None

    @staticmethod
    async def get_by_id(user_id: int) -> Optional[User]:
        """Retrieve a user by ID."""
        return await User.get_or_none(id=user_id)

    @staticmethod
    async def register(
        email: str,
        password: str,
        t: dict,
        **extra_fields: Any
    ) -> User:
        """
        Register a new user with hashed password and assign default tariff.
        Steps:
        1. Check if user already exists.
        2. Validate password strength.
        3. Create user and set password.
        4. Assign default tariff and initial tokens (atomic).
        5. Return user.
        """
        # 1. Normalize and validate email
        validate_email(email, t)
        existing = await UserService.get_by_email(email)
        if existing:
            logger.info(f"Attempt to register already existing user: {email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t["user_already_registered"])

        # 2. Validate password
        try:
            validate_password(password)
        except HTTPException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=t["password_too_weak"]
            )

        # 3 & 4. Create user, assign tariff and tokens atomically
        async with in_transaction():
            user = User(email=email, **extra_fields)
            user.set_password(password)
            await user.save()
            default_tariff = await Tariff.get_default_tariff()
            if default_tariff:
                user.tariff = default_tariff
                user.tokens = default_tariff.tokens
                await user.save()
                await TokenTransaction.create(
                    user=user,
                    transaction_type=TransactionType.DAILY_BONUS,
                    amount=default_tariff.tokens,
                    balance_after_transaction=user.tokens,
                    description=f"Daily bonus for {default_tariff.name}",
                )
        logger.info(f"User registered: {email}")
        return user

    @staticmethod
    async def authenticate(email: str, password: str, t: dict) -> User:
        """
        Authenticate user by email and password.
        Steps:
        1. Retrieve user by email.
        2. Check if user is active.
        3. Verify password.
        4. Check if email is verified.
        5. Return user if all checks pass.
        Raises HTTPException with localization if invalid.
        """
        user = await UserService.get_by_email(email)
        if not user:
            logger.info(f"Login failed, user not found: {email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t["invalid_credentials"])

        if not user.is_active:
            logger.info(f"Login failed, inactive user: {email}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["inactive_user"])

        loop = asyncio.get_event_loop()
        password_valid = await loop.run_in_executor(None, user.check_password, password)
        if not password_valid:
            logger.info(f"Login failed, incorrect password: {email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t["invalid_credentials"])

        if not user.is_verified:
            logger.info(f"Login failed, email not verified: {email}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=t["email_not_verified"])

        return user

    @staticmethod
    async def update_user(
        user_id: int,
        t: dict,
        **fields: Any
    ) -> User:
        """
        Update user fields (non-admin).
        Steps:
        1. Retrieve user.
        2. Check email uniqueness if email is being updated.
        3. Exclude protected fields and update.
        4. Save and return user.
        Raises HTTPException with localization if invalid.
        """
        # 1. Retrieve user
        user = await UserService.get_by_id(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["user_not_found"])

        # 2. Check email uniqueness
        if "email" in fields and fields["email"]:
            validate_email(fields["email"], t)
            existing = await UserService.get_by_email(fields["email"])
            if existing and existing.id != user_id:
                logger.warning(f"Email already in use: {fields['email']}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t["email_already_in_use"])

        # 3. Exclude protected fields
        invalid = set(fields) - ALLOWED_UPDATE_FIELDS
        if invalid:
            logger.warning(f"Attempt to update invalid fields for user {user_id}: {invalid}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid fields for update: {', '.join(invalid)}"
            )
        # 4. Update allowed fields
        for attr, value in fields.items():
            if attr in ALLOWED_UPDATE_FIELDS and value is not None:
                setattr(user, attr, value)
        await user.save()
        logger.info(f"User updated: {user_id}")
        return user

    @staticmethod
    async def admin_update_user(
        user_id: int,
        t: dict,
        **fields: Any
    ) -> User:
        """
        Update user fields (admin only, allows staff/superuser fields).
        Steps:
        1. Retrieve user.
        2. Check for invalid fields.
        3. Check email uniqueness if email is being updated.
        4. Update allowed fields.
        5. Save and return user.
        Raises HTTPException with localization if invalid.
        """
        user = await UserService.get_by_id(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["user_not_found"])

        # 2. Check for invalid fields
        invalid = set(fields) - ADMIN_ALLOWED_UPDATE_FIELDS
        if invalid:
            logger.warning(f"Attempt to update invalid fields for user {user_id}: {invalid}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid fields for update: {', '.join(invalid)}"
            )

        # 3. Check email uniqueness
        if "email" in fields and fields["email"]:
            validate_email(fields["email"], t)
            existing = await UserService.get_by_email(fields["email"])
            if existing and existing.id != user_id:
                logger.warning(f"Email already in use: {fields['email']}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t["email_already_in_use"])

        # 4. Update allowed fields
        for attr, value in fields.items():
            if attr in ADMIN_ALLOWED_UPDATE_FIELDS and value is not None:
                setattr(user, attr, value)
        await user.save()
        logger.info(f"Admin updated user: {user_id}")
        return user

    @staticmethod
    async def change_password(
        user_id: int,
        new_password: str,
        t: dict
    ) -> None:
        """
        Change user's password.
        Steps:
        1. Retrieve user.
        2. Validate password strength.
        3. Set new password and save.
        Raises HTTPException with localization if invalid.
        """
        user = await UserService.get_by_id(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=t["user_not_found"]
            )
        try:
            validate_password(new_password)
        except HTTPException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=t["password_too_weak"]
            )
        user.set_password(new_password)
        await user.save()
        logger.info(f"Password changed for user: {user_id}")

    @staticmethod
    async def delete_user(user_id: int, t: dict) -> None:
        """
        Delete a user.
        Steps:
        1. Retrieve user.
        2. Delete user.
        Raises HTTPException with localization if user not found.
        """
        user = await UserService.get_by_id(user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=t["user_not_found"])
        await user.delete()
        logger.info(f"User deleted: {user_id}")

    @staticmethod
    async def list_users(is_active: Optional[bool] = None) -> list[User]:
        """
        List all users, optionally filtering by active status.
        """
        if is_active is None:
            return await User.all()
        return await User.filter(is_active=is_active)

    @staticmethod
    async def create_user(
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        age: Optional[int] = None,
        photo: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
        is_staff: bool = False,
        is_superuser: bool = False,
    ) -> User:
        """
        Create a new user (admin only, no localization needed).
        """
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            age=age,
            photo=photo,
            is_active=is_active,
            is_verified=is_verified,
            is_staff=is_staff,
            is_superuser=is_superuser
        )
        user.set_password(password)
        await user.save()
        return user
