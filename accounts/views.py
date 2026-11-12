from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import CustomerRegistrationForm, LoginForm, ProviderRegistrationForm


class RepairLinkLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        messages.success(self.request, f"Welcome back, {user.first_name or user.username}!")
        return super().form_valid(form)


def register_customer(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your account has been created. Welcome to RepairLink!")
            return redirect("dashboard:home")
    else:
        form = CustomerRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def register_provider(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = ProviderRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                "Your provider account has been created. An administrator will review your profile.",
            )
            return redirect("dashboard:home")
    else:
        form = ProviderRegistrationForm()
    return render(request, "accounts/provider_register.html", {"form": form})
