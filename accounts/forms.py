from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms
from .models import Breeder

class BreederRegistrationForm(UserCreationForm):
    """
    Formularz przeznaczony do bezpiecznej rejestracji hodowców na stronie.
    """
    class Meta:
        model = Breeder
        fields = ("email", "first_name", "last_name")

# ZMIANA: Dziedziczymy po prostym ModelForm
class BreederCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Hasło")

    class Meta:
        model = Breeder
        fields = ("email", "first_name", "last_name", "password")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) # Tutaj bezpiecznie hashujemy
        if commit:
            user.save()
        return user

class BreederChangeForm(UserChangeForm):
    class Meta:
        model = Breeder
        fields = '__all__'