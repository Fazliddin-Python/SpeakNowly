from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from tortoise.exceptions import DoesNotExist
from passlib.hash import bcrypt

from models.users.users import User
from models.tariffs import Tariff
from models.transactions import TokenTransaction, TransactionType


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
        """
        user = User(email=email, **extra_fields)
        user.set_password(password)
        await user.save()

        # Assign default tariff and initial tokens
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
        return user

    @staticmethod
    async def authenticate(email: str, password: str) -> User:
        """
        Authenticate user by email and password.
        Raises HTTPException if invalid.
        """
        user = await UserService.get_by_email(email)
        if not user or not user.check_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        if not user.is_active:
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
        """
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        # Exclude protected fields
        for attr, value in fields.items():
            if hasattr(user, attr) and value is not None and attr != 'password':
                setattr(user, attr, value)
        await user.save()
        return user

    @staticmethod
    async def change_password(
        user_id: int,
        new_password: str
    ) -> None:
        """
        Change user's password.
        """
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.set_password(new_password)
        await user.save()

    @staticmethod
    async def delete_user(user_id: int) -> None:
        """
        Delete a user.
        """
        user = await UserService.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await user.delete()