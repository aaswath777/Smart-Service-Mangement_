from django.contrib import admin

from .models import Complaint, Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("booking", "provider", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("comment", "provider__user__username")


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ("subject", "user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("subject", "user__username")
