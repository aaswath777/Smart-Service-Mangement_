from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, render

from providers.models import ProviderProfile
from providers.selectors import approved_providers

from .models import ServiceCategory


def service_list(request):
    categories = ServiceCategory.objects.filter(is_active=True).annotate(
        provider_count=Count(
            "providers",
            filter=Q(providers__verification_status=ProviderProfile.VerificationStatus.APPROVED),
            distinct=True,
        )
    )
    return render(request, "services/service_list.html", {"categories": categories})


def service_detail(request, slug):
    category = get_object_or_404(ServiceCategory, slug=slug, is_active=True)
    providers = (
        approved_providers()
        .filter(pk__in=category.providers.values("pk"))
        .order_by(F("rating_avg").desc(nulls_last=True), "-experience_years")
    )
    context = {
        "category": category,
        "services": category.services.filter(is_active=True),
        "providers": providers,
    }
    return render(request, "services/service_detail.html", context)
