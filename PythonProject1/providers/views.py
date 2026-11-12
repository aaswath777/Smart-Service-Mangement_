from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, render

from services.models import Service, ServiceCategory

from .models import ProviderProfile
from .selectors import approved_providers

SORT_OPTIONS = {
    "rating": [F("rating_avg").desc(nulls_last=True), "-rating_count"],
    "experience": ["-experience_years"],
    "newest": ["-created_at"],
}


def _to_number(value, cast):
    """Convert text from the URL to a number, or return None if invalid."""
    try:
        return cast(value)
    except (TypeError, ValueError):
        return None


def provider_list(request):
    providers = approved_providers()

    # Read what the visitor typed or selected (all optional)
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    min_rating = request.GET.get("min_rating", "").strip()
    min_experience = request.GET.get("min_experience", "").strip()
    available = request.GET.get("available") == "on"
    sort = request.GET.get("sort", "rating")

    if q:
        # Providers whose category or service name matches the search text
        matching_ids = ProviderProfile.objects.filter(
            Q(categories__name__icontains=q)
            | Q(categories__services__name__icontains=q)
        ).values("pk")
        providers = providers.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__username__icontains=q)
            | Q(city__icontains=q)
            | Q(service_area__icontains=q)
            | Q(skills__icontains=q)
            | Q(headline__icontains=q)
            | Q(pk__in=matching_ids)
        )

    if category:
        in_category = ProviderProfile.objects.filter(categories__slug=category).values("pk")
        providers = providers.filter(pk__in=in_category)

    rating_value = _to_number(min_rating, float)
    if rating_value is not None:
        providers = providers.filter(rating_avg__gte=rating_value)

    experience_value = _to_number(min_experience, int)
    if experience_value is not None:
        providers = providers.filter(experience_years__gte=experience_value)

    if available:
        providers = providers.filter(is_available=True)

    providers = providers.order_by(*SORT_OPTIONS.get(sort, SORT_OPTIONS["rating"]), "pk")

    paginator = Paginator(providers, 6)  # 6 cards per page
    page_obj = paginator.get_page(request.GET.get("page"))

    # Keep the filters in the page links (everything except "page")
    params = request.GET.copy()
    params.pop("page", None)

    context = {
        "page_obj": page_obj,
        "result_count": paginator.count,
        "categories": ServiceCategory.objects.filter(is_active=True),
        "querystring": params.urlencode(),
        "filters": {
            "q": q,
            "category": category,
            "min_rating": min_rating,
            "min_experience": min_experience,
            "available": available,
            "sort": sort,
        },
        "has_filters": bool(q or category or min_rating or min_experience or available),
    }
    return render(request, "providers/provider_list.html", context)


def provider_detail(request, pk):
    provider = get_object_or_404(approved_providers(), pk=pk)
    context = {
        "provider": provider,
        "reviews": provider.reviews.select_related("customer", "booking__service"),
        "services": Service.objects.filter(
            category__in=provider.categories.all(), is_active=True
        ).select_related("category"),
        "availability": provider.availability.all(),
    }
    return render(request, "providers/provider_detail.html", context)
