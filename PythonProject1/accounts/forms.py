from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from providers.models import ProviderProfile
from services.models import ServiceCategory

from .models import CustomerProfile, User


class BootstrapFormMixin:
    """Adds Bootstrap CSS classes to every field of any form that uses it."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                continue
            css = "form-select" if isinstance(widget, forms.Select) else "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "Your username"
        self.fields["password"].widget.attrs["placeholder"] = "Your password"


class BaseRegistrationForm(BootstrapFormMixin, UserCreationForm):
    """Fields shared by customer and provider registration."""

    email = forms.EmailField()
    phone = forms.CharField(
        max_length=10,
        help_text="10-digit mobile number",
        widget=forms.TextInput(attrs={"placeholder": "9876543210"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "phone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not (phone.isdigit() and len(phone) == 10 and phone[0] in "6789"):
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return phone


class CustomerRegistrationForm(BaseRegistrationForm):
    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)  # password is hashed here
        user.role = User.Role.CUSTOMER
        user.save()
        CustomerProfile.objects.create(user=user)
        return user


class ProviderRegistrationForm(BaseRegistrationForm):
    headline = forms.CharField(
        max_length=120,
        required=False,
        help_text="One line about you, e.g. 'Licensed electrician'",
    )
    city = forms.CharField(max_length=100, initial="Chennai")
    service_area = forms.CharField(
        max_length=150, help_text="Areas you serve, e.g. Velachery, Adyar"
    )
    experience_years = forms.IntegerField(min_value=0, max_value=60, initial=0)
    skills = forms.CharField(
        max_length=255, required=False, help_text="Separate skills with commas"
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Tell customers about your work",
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=ServiceCategory.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        help_text="Choose at least one",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categories"].queryset = ServiceCategory.objects.filter(is_active=True)

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.PROVIDER
        user.save()
        profile = ProviderProfile.objects.create(
            user=user,
            headline=self.cleaned_data["headline"],
            bio=self.cleaned_data["bio"],
            experience_years=self.cleaned_data["experience_years"],
            skills=self.cleaned_data["skills"],
            city=self.cleaned_data["city"],
            service_area=self.cleaned_data["service_area"],
        )  # status defaults to PENDING until an admin approves
        profile.categories.set(self.cleaned_data["categories"])
        return user