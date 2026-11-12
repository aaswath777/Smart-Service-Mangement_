from django.contrib import admin

from .models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "is_active")
    list_editable = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "base_price", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)