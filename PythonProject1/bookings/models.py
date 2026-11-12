from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


class Booking(TimeStampedModel):
    """A customer's request for a service from one provider."""

    class Status(models.TextChoices):
        REQUESTED = "REQUESTED", "Requested"
        ACCEPTED = "ACCEPTED", "Accepted"
        ON_THE_WAY = "ON_THE_WAY", "On the way"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        REJECTED = "REJECTED", "Rejected"

    # Which status may follow which (the workflow rulebook)
    ALLOWED_TRANSITIONS = {
        Status.REQUESTED: [Status.ACCEPTED, Status.REJECTED, Status.CANCELLED],
        Status.ACCEPTED: [Status.ON_THE_WAY, Status.CANCELLED],
        Status.ON_THE_WAY: [Status.IN_PROGRESS],
        Status.IN_PROGRESS: [Status.COMPLETED],
        Status.COMPLETED: [],
        Status.CANCELLED: [],
        Status.REJECTED: [],
    }

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    provider = models.ForeignKey(
        "providers.ProviderProfile",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    address = models.TextField(help_text="Full address where the service is needed")
    problem_description = models.TextField()
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.REQUESTED
    )
    final_price = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["provider", "status"]),
            models.Index(fields=["customer", "-created_at"]),
        ]

    # ---- business rules live inside the class ----
    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS[self.status]

    def can_be_cancelled(self):
        return self.can_transition_to(self.Status.CANCELLED)

    def clean(self):
        if self.customer_id and self.provider_id and self.customer_id == self.provider.user_id:
            raise ValidationError("You cannot book yourself.")
        if self.provider_id and self.service_id:
            offered = self.provider.categories.filter(pk=self.service.category_id)
            if not offered.exists():
                raise ValidationError("This provider does not offer that service category.")

    def __str__(self):
        return f"Booking #{self.pk} - {self.service.name}"