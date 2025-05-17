from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction
from passlib.hash import bcrypt

from models.users.users import User
from models.tariffs import Tariff
from models.transactions import TokenTransaction, TransactionType

import logging

logger = logging.getLogger("user_service")

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
        """Retrieve a user by primary key ID."""
        return await User.get_or_none(id=user_id)

    @staticmethod
    async def register(
        email: str,
        password: str,
        **extra_fields: Any
    ) -> User:
        """
        Register a new user with hashed password and assign default tariff.
        1. Check if user already exists.
        2. Validate password strength.
        3. Create user and set password.
        4. Assign default tariff and initial tokens (atomic).
        5. Return user.
        """
        # 1. Check if user already exists
        existing = await UserService.get_by_email(email)
        if existing:
            logger.info(f"Attempt to register already existing user: {email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered")

        # 2. Validate password strength (simple example, use more strict rules in production)
        if len(password) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password too short (min 8 chars)")

        # 3 & 4. Create user, assign tariff and tokens atomically
        async with in_transaction():
            user = User(email=email, **extra_fields)
            user.set_password(password)
            await user.save()

            default_tariff = await Tariff.filter(is_default=True).first()
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
    async def authenticate(email: str, password: str) -> User:
        """
        Authenticate user by email and password.
        Raises HTTPException if invalid.
        """
        user = await UserService.get_by_email(email)
        if not user or not user.check_password(password):
            logger.info(f"Failed authentication attempt for {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        if not user.is_active:
            logger.info(f"Inactive user tried to authenticate: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        return user

    @staticmethod
    async def update_user(
        user_id: int,
        **fields: Any
    ) -> User:
        """
        Update user fields (excluding password).
        1. Retrieve user.
        2. Check email uniqueness if email is being updated.
        3. Update allowed fields.
        4. Save and return user.
        """
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # 2. Check email uniqueness
        if "email" in fields and fields["email"]:
            existing = await UserService.get_by_email(fields["email"])
            if existing and existing.id != user_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

        # 3. Exclude protected fields and update
        for attr, value in fields.items():
            if hasattr(user, attr) and value is not None and attr != 'password':
                setattr(user, attr, value)
        await user.save()
        logger.info(f"User updated: {user_id}")
        return user

    @staticmethod
    async def change_password(
        user_id: int,
        new_password: str
    ) -> None:
        """
        Change user's password.
        1. Retrieve user.
        2. Validate password strength.
        3. Set new password and save.
        """
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if len(new_password) < 8:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password too short (min 8 chars)")
        user.set_password(new_password)
        await user.save()
        logger.info(f"Password changed for user: {user_id}")

    @staticmethod
    async def delete_user(user_id: int) -> None:
        """
        Delete a user.
        1. Retrieve user.
        2. Delete user.
        """
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await user.delete()
        logger.info(f"User deleted: {user_id}")