from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import redirect, render
from django.contrib import messages

from .forms import BreederRegistrationForm
from .utils import verify_turnstile  # Importujemy naszą nową funkcję!


def home_view(request):
    return render(request, "home_pages/home.html")


def price_list_view(request):
    return render(request, "home_pages/price_list.html")


def login_view(request):
    if request.method == "POST":
        # 1. BRAMKARZ: Weryfikacja Turnstile
        if not verify_turnstile(request):
            messages.error(request, "Weryfikacja bezpieczeństwa nie powiodła się, spróbuj ponownie.")
            form = AuthenticationForm()
            return render(request, "home_pages/login.html", {"form": form})

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

    return render(request, "home_pages/login.html", {"form": form})


def register_view(request):
    if request.method == "POST":
        # 1. BRAMKARZ: Weryfikacja Turnstile
        if not verify_turnstile(request):
            messages.error(request, "Proszę potwierdzić, że nie jesteś robotem.")
            form = BreederRegistrationForm(request.POST)
            return render(request, "home_pages/register.html", {"form": form})

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

    return render(request, "home_pages/register.html", {"form": form})


@login_required
def your_profile_view(request) -> HttpResponse:
    from .models import Breeder

    if request.method == "POST":
        user = request.user
        for field in (
            "first_name", "last_name", "email", "phone_number",
            "kennel_name", "membership_number", "branch", "kennel_registration_number",
        ):
            value = request.POST.get(field)
            if value is not None:
                setattr(user, field, value)
        for field in ("nip", "address_line_one", "address_line_two", "city", "region", "postal_code", "country"):
            if field in request.POST:
                setattr(user, field, request.POST[field])
        user.save()
        messages.success(request, "Dane zostały zaktualizowane.")
        return redirect("your_profile")

    payments = request.user.payments.select_related("plan").order_by("-created_at")
    context = {
        "payments": payments,
        "branch_choices": Breeder.ZKwPBranch.choices,
    }
    return render(request, "dashboard/dashboard_your_profile.html", context)


@login_required
@require_POST
def reveal_sensitive_data_view(request) -> JsonResponse:
    try:
        body = json.loads(request.body)
        password = body.get("password", "")
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Nieprawidłowe żądanie"}, status=400)

    if not request.user.check_password(password):
        return JsonResponse({"error": "Nieprawidłowe hasło"}, status=403)

    user = request.user
    return JsonResponse({
        "nip": user.nip or "—",
        "address_line_one": user.address_line_one or "—",
        "address_line_two": user.address_line_two or "—",
        "city": user.city or "—",
        "region": user.region or "—",
        "postal_code": user.postal_code or "—",
        "country": str(user.country.name) if user.country else "—",
    })