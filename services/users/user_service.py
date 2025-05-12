from models.users.users import User
from tortoise.exceptions import DoesNotExist
from passlib.hash import bcrypt


class UserService:
    @staticmethod
    async def get_user_by_email(email: str) -> User:
        """
        Retrieve a user by email.
        """
        try:
            return await User.get(email=email)
        except DoesNotExist:
            return None

    @staticmethod
    async def create_user(email: str, password: str, **extra_fields) -> User:
        """
        Create a new user.
        """
        user = User(email=email, **extra_fields)
        user.set_password(password)
        await user.save()
        return user

    @staticmethod
    async def update_user(user_id: int, **fields) -> User:
        """
        Update user data.
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("User not found")
        for key, value in fields.items():
            setattr(user, key, value)
        await user.save()
        return user

    @staticmethod
    async def delete_user(user_id: int) -> None:
        """
        Delete a user.
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("User not found")
        await user.delete()