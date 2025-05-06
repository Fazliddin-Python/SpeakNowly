from ..tariffs import Tariff
from tortoise import fields
from ..base import BaseModel
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

    @property
    def is_premium(self):
        """Checks if the user has a premium tariff."""
        if self.tariff is None:
            self.add_tariff(Tariff.get_default_tariff())
        return not self.tariff.is_default

    def add_tariff(self, tariff):
        """Assigns a tariff to the user."""
        self.tariff = tariff
        self.save()


class UserActivityLog(BaseModel):
    user = fields.ForeignKeyField("models.User", related_name="activity_logs", description="User")
    action = fields.CharField(max_length=255, description="Action performed by the user")
    timestamp = fields.DatetimeField(auto_now_add=True, description="Timestamp of the action")

    class Meta:
        table = "user_activity_logs"
        verbose_name = "User Activity Log"
        verbose_name_plural = "User Activity Logs"

    def __str__(self):
        return f"{self.user.email} - {self.action}"