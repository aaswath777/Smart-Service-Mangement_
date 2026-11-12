from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from bookings.models import Booking
from core.models import TimeStampedModel


class Review(TimeStampedModel):
    """A customer's rating of a provider after a COMPLETED booking."""

    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="review"
    )
    # Filled automatically from the booking (see save()).
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_written",
        editable=False,
    )
    provider = models.ForeignKey(
        "providers.ProviderProfile",
        on_delete=models.CASCADE,
        related_name="reviews",
        editable=False,
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__gte=1, rating__lte=5),
                name="rating_between_1_and_5",
            )
        ]

    def clean(self):
        if self.booking_id and self.booking.status != Booking.Status.COMPLETED:
            raise ValidationError("You can only review a completed booking.")

    def save(self, *args, **kwargs):
        self.clean()
        self.customer = self.booking.customer
        self.provider = self.booking.provider
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rating}/5 for {self.provider}"


class Complaint(TimeStampedModel):
    """A complaint raised by a user. Admins read and resolve these."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_REVIEW = "IN_REVIEW", "In review"
        RESOLVED = "RESOLVED", "Resolved"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="complaints",
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaints",
    )
    subject = models.CharField(max_length=150)
    description = models.TextField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OPEN
    )
    admin_response = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"