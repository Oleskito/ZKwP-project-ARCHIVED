from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.contrib import messages

from .forms import BreederRegistrationForm
from .utils import verify_turnstile  # Importujemy naszą nową funkcję!


def home_view(request):
    return render(request, "home.html")


def price_list_view(request):
    return render(request, "price_list.html")


def login_view(request):
    if request.method == "POST":
        # 1. BRAMKARZ: Weryfikacja Turnstile
        if not verify_turnstile(request):
            messages.error(request, "Weryfikacja bezpieczeństwa nie powiodła się, spróbuj ponownie.")
            form = AuthenticationForm()
            return render(request, "login.html", {"form": form})

        # 2. STANDARDOWE LOGOWANIE
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Błędny adres e-mail lub hasło. Spróbuj ponownie.")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def register_view(request):
    if request.method == "POST":
        # 1. BRAMKARZ: Weryfikacja Turnstile
        if not verify_turnstile(request):
            messages.error(request, "Proszę potwierdzić, że nie jesteś robotem.")
            form = BreederRegistrationForm(request.POST)
            return render(request, "register.html", {"form": form})

        # 2. WALIDACJA FORMULARZA REJESTRACJI
        form = BreederRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Konto utworzone pomyślnie! Możesz się zalogować.")
            return redirect("login")
        else:
            print("BŁĘDY WALIDACJI:", form.errors)  # Zostawiamy do ewentualnego debugowania
    else:
        form = BreederRegistrationForm()

    return render(request, "register.html", {"form": form})