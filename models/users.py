from tortoise import fields
from .base import BaseModel
from gettext import gettext as _  # Для перевода строк

class User(BaseModel):
    telegram_id = fields.BigIntField(unique=True, null=True, description=_("Telegram ID"))
    email = fields.CharField(max_length=255, unique=True, description=_("Email Address"))
    age = fields.IntField(null=True, description=_("Age"))
    is_verified = fields.BooleanField(default=False, description=_("Verified"))
    photo = fields.CharField(max_length=255, null=True, description=_("Photo"))  # В Django это ImageField
    tariff = fields.ForeignKeyField('models.Tariff', related_name='users', null=True, description=_("Tariff"))
    tokens = fields.IntField(default=0, null=True, description=_("Tokens"))
    password = fields.CharField(max_length=128, description=_("Password"))
    is_active = fields.BooleanField(default=True, description=_("Active"))
    is_staff = fields.BooleanField(default=False, description=_("Staff"))
    is_superuser = fields.BooleanField(default=False, description=_("Superuser"))
    last_login = fields.DatetimeField(null=True, description=_("Last Login"))

    class Meta:
        table = "users"

class VerificationCode(BaseModel):
    REGISTER = "register"
    LOGIN = "login"
    RESET_PASSWORD = "reset_password"
    FORGET_PASSWORD = "forget_password"
    UPDATE_EMAIL = "update_email"

    VERIFICATION_TYPES = (
        (REGISTER, _("Register")),
        (LOGIN, _("Login")),
        (RESET_PASSWORD, _("Reset Password")),
        (FORGET_PASSWORD, _("Forget Password")),
        (UPDATE_EMAIL, _("Update Email")),
    )

    email = fields.CharField(max_length=255, null=True, description=_("Email"))
    user = fields.ForeignKeyField('models.User', related_name='verification_codes', null=True, description=_("User"))
    verification_type = fields.CharField(
        max_length=255,
        choices=VERIFICATION_TYPES,
        description=_("Verification Type")
    )
    code = fields.IntField(
        null=True,
        description=_("Code")
    )
    is_used = fields.BooleanField(default=False, description=_("Used"))
    is_expired = fields.BooleanField(default=False, description=_("Expired"))

    class Meta:
        table = "verification_codes"