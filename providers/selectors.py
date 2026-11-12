from django.db.models import Avg, Count

from .models import ProviderProfile


def approved_providers():
    """
    Providers that an administrator approved, each with two extra values
    computed by the database: rating_avg and rating_count.
    Only approved providers are ever shown to customers.
    """
    return (
        ProviderProfile.objects.filter(
            verification_status=ProviderProfile.VerificationStatus.APPROVED
        )
        .select_related("user")
        .prefetch_related("categories")
        .annotate(rating_avg=Avg("reviews__rating"), rating_count=Count("reviews"))
    )