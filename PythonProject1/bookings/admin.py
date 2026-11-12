from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id", "customer", "provider", "service",
        "scheduled_date", "scheduled_time", "status",
    )
    list_filter = ("status", "scheduled_date")
    search_fields = ("customer__username", "provider__user__username", "address")
    date_hierarchy = "scheduled_date"