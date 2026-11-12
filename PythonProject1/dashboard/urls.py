from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("dashboard/", views.home, name="home"),
    path("dashboard/customer/", views.customer_dashboard, name="customer"),
    path("dashboard/customer/profile/", views.customer_profile, name="customer_profile"),
    path("dashboard/provider/", views.provider_dashboard, name="provider"),
    path("dashboard/admin/", views.admin_dashboard, name="admin"),
]