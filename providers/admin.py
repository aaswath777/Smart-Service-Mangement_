from django.contrib import admin

from .models import ProviderAvailability, ProviderProfile


@admin.action(description="Approve selected providers")
def approve_providers(modeladmin, request, queryset):
    queryset.update(verification_status=ProviderProfile.VerificationStatus.APPROVED)


@admin.action(description="Reject selected providers")
def reject_providers(modeladmin, request, queryset):
    queryset.update(verification_status=ProviderProfile.VerificationStatus.REJECTED)


class AvailabilityInline(admin.TabularInline):
    model = ProviderAvailability
    extra = 0


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "city", "experience_years", "verification_status", "is_available",
    )
    list_filter = ("verification_status", "is_available", "city", "categories")
    search_fields = ("user__username", "user__first_name", "user__last_name", "city")
    filter_horizontal = ("categories",)
    inlines = [AvailabilityInline]
    actions = [approve_providers, reject_providers]


@admin.register(ProviderAvailability)
class ProviderAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("provider", "weekday", "start_time", "end_time")
    list_filter = ("weekday",)