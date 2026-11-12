from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import get_effective_role, role_required
from accounts.models import User
from bookings.models import Booking
from providers.models import ProviderProfile
from reviews.models import Review
from services.models import ServiceCategory

from .forms import CustomerProfileForm

ACTIVE_STATUSES = [
    Booking.Status.REQUESTED,
    Booking.Status.ACCEPTED,
    Booking.Status.ON_THE_WAY,
    Booking.Status.IN_PROGRESS,
]


@login_required
def home(request):
    """Send each user to the dashboard that matches their role."""
    role = get_effective_role(request.user)
    if role == User.Role.ADMIN:
        return redirect("dashboard:admin")
    if role == User.Role.PROVIDER:
        return redirect("dashboard:provider")
    return redirect("dashboard:customer")


# ---------------------------------------------------------------
# CUSTOMER
# ---------------------------------------------------------------
@role_required(User.Role.CUSTOMER)
def customer_dashboard(request):
    today = timezone.localdate()
    bookings = Booking.objects.filter(customer=request.user).select_related(
        "provider__user", "service"
    )
    upcoming = (
        bookings.filter(status__in=ACTIVE_STATUSES, scheduled_date__gte=today)
        .order_by("scheduled_date", "scheduled_time")
        .first()
    )
    stats = [
        {"label": "Total bookings", "value": bookings.count(), "icon": "bi-calendar-check-fill"},
        {"label": "Active bookings", "value": bookings.filter(status__in=ACTIVE_STATUSES).count(), "icon": "bi-hourglass-split"},
        {"label": "Completed", "value": bookings.filter(status=Booking.Status.COMPLETED).count(), "icon": "bi-check-circle-fill"},
        {"label": "Unread notifications", "value": request.user.notifications.filter(is_read=False).count(), "icon": "bi-bell-fill"},
    ]
    context = {
        "active_nav": "dashboard",
        "stats": stats,
        "upcoming": upcoming,
        "recent_bookings": bookings[:5],
        "categories": ServiceCategory.objects.filter(is_active=True)[:8],
        "notifications": request.user.notifications.all()[:5],
    }
    return render(request, "dashboard/customer.html", context)


@role_required(User.Role.CUSTOMER)
def customer_profile(request):
    form = CustomerProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your profile has been updated.")
        return redirect("dashboard:customer_profile")
    return render(
        request,
        "dashboard/customer_profile.html",
        {"form": form, "active_nav": "profile"},
    )


# ---------------------------------------------------------------
# PROVIDER (starter page, replaced in Phase 7)
# ---------------------------------------------------------------
@role_required(User.Role.PROVIDER)
def provider_dashboard(request):
    profile = getattr(request.user, "provider_profile", None)
    notice = None
    stats = []

    if profile is None:
        notice = "Your provider profile is missing. Please contact an administrator."
    else:
        if not profile.is_approved:
            notice = (
                f"Your profile status is: {profile.get_verification_status_display()}. "
                "Once an administrator approves it, you will appear in search results."
            )
        stats = [
            {"label": "Pending requests", "value": profile.bookings.filter(status=Booking.Status.REQUESTED).count(), "icon": "bi-inbox-fill"},
            {"label": "Completed jobs", "value": profile.bookings.filter(status=Booking.Status.COMPLETED).count(), "icon": "bi-check-circle-fill"},
            {"label": "Average rating", "value": profile.average_rating() or "No reviews", "icon": "bi-star-fill"},
            {"label": "Verification", "value": profile.get_verification_status_display(), "icon": "bi-patch-check-fill"},
        ]

    context = {
        "title": "Provider Dashboard",
        "role_label": "Service Provider",
        "stats": stats,
        "notice": notice,
        "next_phase": "Phase 7 will replace this page with the full provider dashboard (booking requests, availability and earnings).",
    }
    return render(request, "dashboard/home.html", context)


# ---------------------------------------------------------------
# ADMIN (starter page, replaced in Phase 10)
# ---------------------------------------------------------------
@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    pending = ProviderProfile.objects.filter(
        verification_status=ProviderProfile.VerificationStatus.PENDING
    ).count()
    stats = [
        {"label": "Total users", "value": User.objects.count(), "icon": "bi-people-fill"},
        {"label": "Providers", "value": ProviderProfile.objects.count(), "icon": "bi-person-gear"},
        {"label": "Bookings", "value": Booking.objects.count(), "icon": "bi-calendar-check-fill"},
        {"label": "Reviews", "value": Review.objects.count(), "icon": "bi-star-fill"},
    ]
    notice = None
    if pending:
        notice = f"{pending} provider(s) are waiting for approval. Approve them in the Django admin under Providers."
    context = {
        "title": "Admin Dashboard",
        "role_label": "Administrator",
        "stats": stats,
        "notice": notice,
        "next_phase": "Phase 10 will replace this page with the full admin dashboard with charts and management tools.",
    }
    return render(request, "dashboard/home.html", context)
