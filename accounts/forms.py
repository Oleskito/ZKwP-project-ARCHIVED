from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Breeder


class BreederRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '********'}),
        label="Hasło"
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '********'}),
        label="Powtórz hasło"
    )

    class Meta:
        model = get_user_model()
        fields = ("email", "first_name", "last_name")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError("Hasła nie są identyczne!")
            else:
                validate_password(password)

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise ValidationError("Konto o podanym adresie e-mail już istnieje.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class BreederCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Hasło")

    class Meta:
        model = Breeder
        fields = ("email", "first_name", "last_name", "password")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class BreederChangeForm(UserChangeForm):
    class Meta:
        model = Breeder
        fields = '__all__'