import asyncio
from typing import Optional, Any
from fastapi import HTTPException, status
from tortoise.transactions import in_transaction
from pydantic import validate_email as pydantic_validate_email, ValidationError

from models.users.users import User
from models.tariffs import Tariff
from models.transactions import TokenTransaction, TransactionType

ALLOWED_UPDATE_FIELDS = {
    "email", "first_name", "last_name", "age", "photo", "last_login",
    "is_active", "is_verified"
}
ADMIN_ALLOWED_UPDATE_FIELDS = ALLOWED_UPDATE_FIELDS | {"is_staff", "is_superuser"}


def validate_email(email: str, t: dict):
    """Validate email format."""
    try:
        pydantic_validate_email(email)
    except ValidationError:
        raise HTTPException(status_code=400, detail=t["invalid_email_format"])


def validate_password(password: str, t: dict):
    """Validate password strength."""
    if len(password) < 8:
        raise HTTPException(status_code=400, detail=t["password_too_weak"])
    if password.isdigit() or password.isalpha():
        raise HTTPException(status_code=400, detail=t["password_too_weak"])


class UserService:
    """User CRUD and authentication service."""

    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        """Get user by email."""
        return await User.get_or_none(email=email)

    @staticmethod
    async def get_by_id(user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await User.get_or_none(id=user_id)

    @staticmethod
    async def register(email: str, password: str, t: dict, **extra_fields) -> User:
        """Register a new user with default tariff and tokens."""

        # 1. Validate email
        validate_email(email, t)
        existing = await UserService.get_by_email(email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=t["user_already_registered"])

        # 2. Validate password
        validate_password(password, t)

        # 3. Create user and assign default tariff/tokens atomically
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

        return user

    @staticmethod
    async def authenticate(email: str, password: str, t: dict) -> User:
        """Authenticate user by email and password."""

        # 1. Get user by email
        user = await UserService.get_by_email(email)
        if not user:
            raise HTTPException(status_code=400, detail=t["invalid_credentials"])

        # 2. Check if user is active
        if not user.is_active:
            raise HTTPException(status_code=403, detail=t["inactive_user"])

        # 3. Check password
        loop = asyncio.get_event_loop()
        valid = await loop.run_in_executor(None, user.check_password, password)
        if not valid:
            raise HTTPException(status_code=400, detail=t["invalid_credentials"])

        # 4. Check if email is verified
        if not user.is_verified:
            raise HTTPException(status_code=403, detail=t["email_not_verified"])

        return user

    @staticmethod
    async def update_user(user_id: int, t: dict, **fields) -> User:
        """Update user profile (non-admin)."""

        # 1. Get user
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=t["user_not_found"])

        # 2. Validate email if changed
        if "email" in fields and fields["email"]:
            validate_email(fields["email"], t)
            existing = await UserService.get_by_email(fields["email"])
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail=t["email_already_in_use"])

        # 3. Check for invalid fields
        invalid = set(fields) - ALLOWED_UPDATE_FIELDS
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid fields: {', '.join(invalid)}")

        # 4. Update allowed fields
        for attr, value in fields.items():
            if attr in ALLOWED_UPDATE_FIELDS and value is not None:
                setattr(user, attr, value)
        await user.save()

        return user

    @staticmethod
    async def admin_update_user(user_id: int, t: dict, **fields) -> User:
        """Update user profile (admin, can set staff/superuser)."""

        # 1. Get user
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=t["user_not_found"])

        # 2. Check for invalid fields
        invalid = set(fields) - ADMIN_ALLOWED_UPDATE_FIELDS
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid fields: {', '.join(invalid)}")

        # 3. Validate email if changed
        if "email" in fields and fields["email"]:
            validate_email(fields["email"], t)
            existing = await UserService.get_by_email(fields["email"])
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail=t["email_already_in_use"])

        # 4. Update allowed fields
        for attr, value in fields.items():
            if attr in ADMIN_ALLOWED_UPDATE_FIELDS and value is not None:
                setattr(user, attr, value)
        await user.save()

        return user

    @staticmethod
    async def change_password(user_id: int, new_password: str, t: dict) -> None:
        """Change user password."""

        # 1. Get user
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=t["user_not_found"])

        # 2. Validate password
        validate_password(new_password, t)

        # 3. Set new password
        user.set_password(new_password)
        await user.save()

    @staticmethod
    async def delete_user(user_id: int, t: dict) -> None:
        """Delete user."""

        # 1. Get user
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=t["user_not_found"])

        # 2. Delete user
        await user.delete()

    @staticmethod
    async def list_users(is_active: Optional[bool] = None) -> list[User]:
        """List users, optionally filter by active status."""

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
        """Create user (admin only)."""

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
