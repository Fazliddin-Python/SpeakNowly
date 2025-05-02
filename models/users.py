from models.tariffs import Tariff
from tortoise import fields
from .base import BaseModel
from gettext import gettext as _
from passlib.hash import bcrypt  # For password hashing

class User(BaseModel):
    telegram_id = fields.BigIntField(unique=True, null=True, description="Telegram ID")
    email = fields.CharField(max_length=255, unique=True, description="Email Address")
    age = fields.IntField(null=True, description="Age")
    is_verified = fields.BooleanField(default=False, description="Verified")
    photo = fields.CharField(max_length=255, null=True, description="Photo")
    tariff = fields.ForeignKeyField('models.Tariff', related_name='users', null=True, description="Tariff")
    tokens = fields.IntField(default=0, null=True, description="Tokens")
    password = fields.CharField(max_length=128, description="Password")
    is_active = fields.BooleanField(default=True, description="Active")
    is_staff = fields.BooleanField(default=False, description="Staff")
    is_superuser = fields.BooleanField(default=False, description="Superuser")
    last_login = fields.DatetimeField(null=True, description="Last Login")

    class Meta:
        table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    def set_password(self, raw_password: str):
        """Hashes the password before saving."""
        self.password = bcrypt.hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Checks the password."""
        return bcrypt.verify(raw_password, self.password)


class VerificationCode(BaseModel):
    REGISTER = "register"
    LOGIN = "login"
    RESET_PASSWORD = "reset_password"
    FORGET_PASSWORD = "forget_password"
    UPDATE_EMAIL = "update_email"

    VERIFICATION_TYPES = (
        (REGISTER, "Register"),
        (LOGIN, "Login"),
        (RESET_PASSWORD, "Reset Password"),
        (FORGET_PASSWORD, "Forget Password"),
        (UPDATE_EMAIL, "Update Email"),
    )

    email = fields.CharField(max_length=255, null=True, description="Email")
    user = fields.ForeignKeyField('models.User', related_name='verification_codes', null=True, description="User")
    verification_type = fields.CharField(max_length=255, choices=VERIFICATION_TYPES, description="Verification Type")
    code = fields.IntField(null=True, description="Code")
    is_used = fields.BooleanField(default=False, description="Used")
    is_expired = fields.BooleanField(default=False, description="Expired")

    class Meta:
        table = "verification_codes"
        verbose_name = "Verification Code"
        verbose_name_plural = "Verification Codes"

    def __str__(self):
        return f"{self.verification_type} - {self.email}"

    def is_code_expired(self) -> bool:
        """Checks if the code has expired."""
        return self.is_expired