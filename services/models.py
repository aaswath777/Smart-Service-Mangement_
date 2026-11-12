from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from core.models import TimeStampedModel


class ServiceCategory(TimeStampedModel):
    """A group of services, e.g. 'AC Service'. Admins can add more any time."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(
        max_length=50,
        default="bi-tools",
        help_text="A Bootstrap Icons class name, e.g. bi-snow2",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "service categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Service(TimeStampedModel):
    """A specific job inside a category, e.g. 'AC Gas Refill'."""

    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.CASCADE,
        related_name="services",
    )
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Starting price in rupees",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "name"],
                name="unique_service_per_category",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.category.name})"