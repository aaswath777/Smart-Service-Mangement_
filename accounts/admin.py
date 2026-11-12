from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, CustomerProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("RepairLink", {"fields": ("role", "phone")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("RepairLink", {"fields": ("role", "phone")}),
    )
    list_display = ("username", "email", "role", "is_staff")
    list_filter = UserAdmin.list_filter + ("role",)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__username", "user__first_name")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "city", "pincode", "is_default")
    list_filter = ("city", "is_default")
    search_fields = ("user__username", "line1", "city")
