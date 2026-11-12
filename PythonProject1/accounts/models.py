from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from core.models import TimeStampedModel


class User(AbstractUser):
    """
    RepairLink user. Inherits everything from Django's built-in
    AbstractUser (username, password hashing, email, etc.)
    and adds a role and phone number.
    """

    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        PROVIDER = "PROVIDER", "Service Provider"
        ADMIN = "ADMIN", "Administrator"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_provider(self):
        return self.role == self.Role.PROVIDER

    @property
    def is_platform_admin(self):
        return self.role == self.Role.ADMIN


class CustomerProfile(TimeStampedModel):
    """Extra information that only customers have (1 user = 1 profile)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="customer_profile",
    )
    profile_picture = models.ImageField(upload_to="customers/", blank=True)

    def __str__(self):
        return f"Customer profile: {self.user}"


class Address(TimeStampedModel):
    """A saved address. One user can have many addresses."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(max_length=30, default="Home")
    line1 = models.CharField("Address line", max_length=255)
    area = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default="Tamil Nadu")
    pincode = models.CharField(
        max_length=6,
        validators=[RegexValidator(r"^\d{6}$", "Enter a valid 6-digit pincode.")],
    )
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "addresses"
        ordering = ["-is_default", "-created_at"]

    def full_address(self):
        parts = [self.line1, self.area, self.city, self.state, self.pincode]
        return ", ".join(p for p in parts if p)

    def __str__(self):
        return f"{self.label}: {self.full_address()}"