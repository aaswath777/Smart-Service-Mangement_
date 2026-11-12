from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models import Avg, F, Q

from core.models import TimeStampedModel


class ProviderProfile(TimeStampedModel):
    """Professional profile of a service provider (1 user = 1 profile)."""

    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_profile",
    )
    profile_picture = models.ImageField(upload_to="providers/", blank=True)
    headline = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    experience_years = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(60)]
    )
    skills = models.CharField(
        max_length=255, blank=True, help_text="Separate skills with commas"
    )
    city = models.CharField(max_length=100)
    service_area = models.CharField(max_length=150, help_text="e.g. Velachery, Adyar")
    categories = models.ManyToManyField(
        "services.ServiceCategory", related_name="providers", blank=True
    )
    verification_status = models.CharField(
        max_length=10,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["verification_status"]),
            models.Index(fields=["city"]),
        ]

    def clean(self):
        if self.user_id and self.user.role != self.user.Role.PROVIDER:
            raise ValidationError("The linked user must have the Service Provider role.")

    # ---- behaviour (methods) kept inside the class: encapsulation ----
    def average_rating(self):
        result = self.reviews.aggregate(avg=Avg("rating"))["avg"]
        return round(result, 1) if result else 0

    def review_count(self):
        return self.reviews.count()

    def skill_list(self):
        return [s.strip() for s in self.skills.split(",") if s.strip()]

    @property
    def is_approved(self):
        return self.verification_status == self.VerificationStatus.APPROVED

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class ProviderAvailability(TimeStampedModel):
    """Working hours of a provider for one weekday."""

    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    provider = models.ForeignKey(
        ProviderProfile, on_delete=models.CASCADE, related_name="availability"
    )
    weekday = models.IntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name_plural = "provider availability"
        ordering = ["provider", "weekday"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "weekday"], name="one_slot_per_provider_day"
            ),
            models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="end_time_after_start_time",
            ),
        ]

    def __str__(self):
        return f"{self.provider} - {self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"
