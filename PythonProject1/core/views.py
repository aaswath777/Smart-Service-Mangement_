from django.db.models import Count, F, Q
from django.shortcuts import render

from providers.models import ProviderProfile
from providers.selectors import approved_providers
from reviews.models import Review
from services.models import ServiceCategory


def home(request):
    categories = (
        ServiceCategory.objects.filter(is_active=True)
        .annotate(
            provider_count=Count(
                "providers",
                filter=Q(providers__verification_status=ProviderProfile.VerificationStatus.APPROVED),
                distinct=True,
            )
        )
        .order_by("-provider_count", "name")
    )
    featured = approved_providers().order_by(
        F("rating_avg").desc(nulls_last=True), "-experience_years"
    )[:3]
    reviews = (
        Review.objects.select_related("customer", "provider__user", "booking__service")
        .exclude(comment="")[:3]
    )
    context = {
        "category_count": categories.count(),
        "popular_categories": categories[:6],
        "featured_providers": featured,
        "reviews": reviews,
    }
    return render(request, "core/home.html", context)