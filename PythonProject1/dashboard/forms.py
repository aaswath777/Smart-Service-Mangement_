from django import forms

from accounts.forms import BootstrapFormMixin
from accounts.models import User


class CustomerProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True
        self.fields["phone"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        taken = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        if not (phone.isdigit() and len(phone) == 10 and phone[0] in "6789"):
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return phone