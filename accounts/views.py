from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.contrib import messages
from django.conf import settings
import requests

from .forms import BreederRegistrationForm


@login_required
def home_view(request):
    return render(request, "home.html")

def price_list_view(request):
    return render(request, "price_list.html")

def login_view(request):
    if request.method == "POST":
        turnstile_token = request.POST.get('cf-turnstile-response')
        secret_key = settings.TURNSTILE_SECRET_KEY

        verify_url = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'
        data = {
            "secret": secret_key,
            "response": turnstile_token,
        }
        response = requests.post(verify_url, data=data)
        outcome = response.json()

        if not outcome.get("success"):
            messages.error(request, "Weryfikacja bezpieczeństwa nie powiodła się, spróbuj ponownie.")
            form = AuthenticationForm()
            return render(request, "login.html", {"form":form})

        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Błędny email lub haslo")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form":form})


def register_view(request):
    if request.method == "POST":
        form = BreederRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = BreederRegistrationForm()
    return render(request, "register.html", {"form": form})
