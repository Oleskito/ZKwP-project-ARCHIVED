import json
import logging
import re
from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BreederRegistrationForm
from .utils import verify_turnstile


def home_view(request):
    return render(request, "home_pages/home.html")


def price_list_view(request) -> HttpResponse:
    from django.conf import settings as django_settings

    context = {"stripe_public_key": django_settings.STRIPE_PUBLIC_KEY}
    return render(request, "home_pages/price_list.html", context)


def login_view(request):
    if request.method == "POST":
        # 1. BRAMKARZ: Weryfikacja Turnstile
        if not verify_turnstile(request):
            messages.error(
                request,
                "Weryfikacja bezpieczeństwa nie powiodła się, spróbuj ponownie.",
            )
            form = AuthenticationForm()
            return render(request, "home_pages/login.html", {"form": form})

        # 2. STANDARDOWE LOGOWANIE
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if request.POST.get("remember-me"):
                request.session.set_expiry(30 * 24 * 60 * 60)
            else:
                request.session.set_expiry(0)
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
            try:
                from billing.models import SubscriptionPlan

                user = form.save(commit=False)

                plan_name = "Start"
                plan_interval = "monthly"

                try:
                    plan = SubscriptionPlan.objects.get(
                        name__iexact=plan_name,
                        interval__iexact=plan_interval,
                    )
                except SubscriptionPlan.DoesNotExist:
                    plan = None

                now = timezone.now()
                user.current_plan = plan
                user.subscription_activated_at = now
                user.subscription_valid_until = now + relativedelta(months=2)
                user.save()
            except Exception as e:
                logging.getLogger(__name__).exception("Błąd podczas zapisu użytkownika")
                messages.error(request, "Wystąpił błąd podczas tworzenia konta. Spróbuj ponownie.")
                messages.error(request, f"Szczegóły błędu: {str(e)}")
                return render(request, "home_pages/register.html", {"form": form})
            messages.success(request, "Konto utworzone! Możesz się teraz zalogować.")
            return redirect("login")
        else:
            messages.error(request, "Formularz zawiera błędy. Popraw pola zaznaczone na czerwono.")
    else:
        form = BreederRegistrationForm()

    return render(request, "home_pages/register.html", {"form": form})


@login_required
def your_profile_view(request) -> HttpResponse:
    from .models import Breeder

    if request.method == "POST":
        user = request.user
        for field in (
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "kennel_name",
            "membership_number",
            "branch",
            "kennel_registration_number",
        ):
            value = request.POST.get(field)
            if value is not None:
                setattr(user, field, value)
        for field in (
            "nip",
            "address_line_one",
            "address_line_two",
            "city",
            "region",
            "postal_code",
            "country",
            "tax_office",
        ):
            if field in request.POST:
                setattr(user, field, request.POST[field])

        if "pesel" in request.POST:
            pesel_value = request.POST["pesel"].strip()
            if pesel_value and not re.match(r"^\d{11}$", pesel_value):
                messages.error(request, "PESEL musi składać się z dokładnie 11 cyfr.")
                return redirect("your_profile")
            user.pesel = pesel_value or None

        if "birth_date" in request.POST:
            birth_date_value = request.POST["birth_date"]
            if birth_date_value:
                try:
                    user.birth_date = date.fromisoformat(birth_date_value)
                except ValueError:
                    messages.error(request, "Nieprawidłowy format daty urodzenia.")
                    return redirect("your_profile")
            else:
                user.birth_date = None

        user.save()
        if user.stripe_customer_id:
            try:
                import stripe
                # Nadpisujemy adres e-mail w obiekcie Customer w Stripe
                stripe.Customer.modify(
                    user.stripe_customer_id,
                    email=user.email,
                )
            except Exception as e:
                # Rejestrujemy błąd w logach, ale NIE przerywamy działania aplikacji.
                # Dzięki temu, nawet jeśli Stripe ma awarię, hodowca i tak zapisze profil.
                logging.getLogger(__name__).warning("Błąd aktualizacji e-maila w Stripe dla usera %s: %s", user.id,
                                                    str(e))
        messages.success(request, "Dane zostały zaktualizowane.")
        return redirect("your_profile")

    from billing.stripe_utils import PRICE_IDS

    payments = request.user.payments.select_related("plan").order_by("-created_at")
    current_plan_price_id = ""
    if request.user.current_plan:
        plan = request.user.current_plan
        current_plan_price_id = PRICE_IDS.get((plan.name, plan.interval), "")

    context = {
        "payments": payments,
        "branch_choices": Breeder.ZKwPBranch.choices,
        "current_plan_price_id": current_plan_price_id,
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
    return JsonResponse(
        {
            "nip": user.nip or "—",
            "pesel": user.pesel or "—",
            "tax_office": user.tax_office or "—",
            "address_line_one": user.address_line_one or "—",
            "address_line_two": user.address_line_two or "—",
            "city": user.city or "—",
            "region": user.region or "—",
            "postal_code": user.postal_code or "—",
            "country": str(user.country.name) if user.country else "—",
        }
    )
