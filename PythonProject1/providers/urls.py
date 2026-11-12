from django.urls import path

from . import views

app_name = "providers"

urlpatterns = [
    path("", views.provider_list, name="list"),
    path("<int:pk>/", views.provider_detail, name="detail"),
]