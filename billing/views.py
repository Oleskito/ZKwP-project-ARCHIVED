import logging
from datetime import timedelta

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing.models import Payment, SubscriptionPlan
from billing.stripe_utils import PRICE_ID_TO_PLAN, VALID_PRICE_IDS

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
stripe.api_version = "2026-04-22.dahlia"


@login_required
@require_POST
def create_checkout_session_view(request) -> HttpResponse:
    price_id = request.POST.get("price_id", "")
    if price_id not in VALID_PRICE_IDS:
        messages.error(request, "Nieprawidłowy plan. Wybierz plan z listy.")
        return redirect("price_list")

    is_topup = request.POST.get("checkout_type") == "topup"
    mode = "payment" if is_topup else "subscription"

    # Przygotowujemy bazowe parametry sesji
    session_kwargs = {
        "mode": mode,
        "client_reference_id": str(request.user.id),
        "locale": "pl",
        "metadata": {
            "price_id": price_id
        },  # KRYTYCZNE: Webhook potrzebuje tego w obu trybach!
        "success_url": request.build_absolute_uri("/billing/success/"),
        "cancel_url": request.build_absolute_uri("/billing/cancel/"),
    }

    # Logika przypisania STAŁEGO klienta Stripe
    if request.user.stripe_customer_id:
        session_kwargs["customer"] = request.user.stripe_customer_id
    else:
        session_kwargs["customer_email"] = request.user.email

    try:
        if is_topup:
            plan_key = PRICE_ID_TO_PLAN.get(price_id)
            plan_name, interval = plan_key
            plan = SubscriptionPlan.objects.get(name=plan_name, interval=interval)

            session_kwargs["line_items"] = [
                {
                    "quantity": 1,
                    "price_data": {
                        "currency": "pln",
                        "unit_amount": int(plan.price * 100),
                        "product_data": {"name": f"Plan {plan.name} – Doładowanie"},
                    },
                }
            ]
            session_kwargs["invoice_creation"] = {"enabled": True}
        else:
            # Tryb subskrypcji (karta)
            session_kwargs["line_items"] = [{"price": price_id, "quantity": 1}]

        session = stripe.checkout.Session.create(**session_kwargs)

    except Exception:
        logger.exception(
            "Stripe checkout session creation failed for user %s", request.user.id
        )
        messages.error(request, "Wystąpił błąd przy przetwarzaniu płatności.")
        return redirect("price_list")

    return redirect(session.url, permanent=False)


@login_required
@require_POST
def create_portal_session_view(request) -> HttpResponse:
    user = request.user
    if not user.stripe_customer_id:
        messages.error(
            request,
            "Brak aktywnej subskrypcji kartą. Portal jest dostępny tylko dla użytkowników z kartą kredytową.",
        )
        return redirect("your_profile")
    try:
        portal = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=request.build_absolute_uri("/dashboard/profile/"),
        )
    except Exception:
        logger.exception("Stripe portal session creation failed for user %s", user.id)
        messages.error(
            request, "Nie można otworzyć portalu zarządzania. Spróbuj ponownie."
        )
        return redirect("your_profile")
    return redirect(portal.url, permanent=False)


@login_required
def checkout_success_view(request) -> HttpResponse:
    return render(request, "billing/checkout_success.html")


def checkout_cancel_view(request) -> HttpResponse:
    messages.info(
        request, "Anulowałeś płatność. Możesz wybrać plan w dowolnym momencie."
    )
    return redirect("price_list")


@csrf_exempt
def stripe_webhook_view(request) -> HttpResponse:
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print(f"❌ BLAD WEBHOOKA (Sygnatura/JSON): {e}")
        return HttpResponse(status=400)

    print(f"\n✅ OTRZYMANO WEBHOOK ZE STRIPE: {event.type}")

    if event.type == "checkout.session.completed":
        print("🚀 URUCHAMIAM LOGIKE ZAPISU PLATNOSCI")
        try:
            _handle_checkout_completed(event.data.object)
            print("✅ CALY PROCES ZAKONCZONY POMYSLNIE")
        except Exception as e:
            print(f"❌ KRYTYCZNY BŁĄD W KODZIE WEBHOOKA: {e}")
            import traceback

            traceback.print_exc()
    else:
        print("⏭️ Ignoruje ten typ zdarzenia (to nie jest zakończenie kasy).")

    return HttpResponse(status=200)


def _handle_checkout_completed(session):
    user_id = getattr(session, "client_reference_id", None)
    if not user_id:
        return

    User = get_user_model()
    try:
        breeder = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    # KROK 1: Aktualizacja ID Stripe w bazie
    customer_id = getattr(session, "customer", None)
    subscription_id = getattr(session, "subscription", None)
    stripe_fields = []
    if not breeder.stripe_customer_id and customer_id:
        breeder.stripe_customer_id = customer_id
        stripe_fields.append("stripe_customer_id")
    if not breeder.stripe_subscription_id and subscription_id:
        breeder.stripe_subscription_id = subscription_id
        stripe_fields.append("stripe_subscription_id")
    if stripe_fields:
        breeder.save(update_fields=stripe_fields)

    # KROK 2: Odczyt planu z webhooka
    metadata = getattr(session, "metadata", None)
    price_id = getattr(metadata, "price_id", "") if metadata else ""
    if not price_id and hasattr(metadata, "get"):
        price_id = metadata.get("price_id", "")

    plan_key = PRICE_ID_TO_PLAN.get(price_id)
    if not plan_key:
        return

    plan_name, interval = plan_key
    try:
        plan = SubscriptionPlan.objects.get(
            name__iexact=plan_name, interval__iexact=interval
        )
    except SubscriptionPlan.DoesNotExist:
        return

    now = timezone.now()

    # KROK 3: MATEMATYKA PRORACJI (Z załataniem Trial Exploit i Planów Rocznych)
    remaining_days = 0
    if breeder.subscription_valid_until and breeder.subscription_valid_until > now:
        remaining_days = (breeder.subscription_valid_until - now).days

    # SPRAWDZAMY CZY UŻYTKOWNIK JEST NA DARMOWYM TRIALU
    # Jeśli nie ma żadnej opłaconej transakcji, to jego dni są "darmowe"
    has_paid = Payment.objects.filter(
        breeder=breeder, status=Payment.Status.COMPLETED
    ).exists()

    # DYNAMICZNY DZIELNIK CZASU (30 czy 365 dni)
    old_days_in_cycle = (
        365
        if (breeder.current_plan and breeder.current_plan.interval == "yearly")
        else 30
    )
    new_days_in_cycle = 365 if plan.interval == "yearly" else 30

    # WARTOŚĆ STAREGO PLANU (0 zł, jeśli to darmowy Trial!)
    if has_paid:
        old_price = float(breeder.current_plan.price) if breeder.current_plan else 0.0
    else:
        old_price = 0.0

    new_price = float(plan.price)

    # STAWKI DZIENNE
    old_daily_rate = old_price / old_days_in_cycle if old_price > 0 else 0.0
    new_daily_rate = new_price / new_days_in_cycle if new_price > 0 else 0.0

    extra_days = 0
    days_to_add = new_days_in_cycle

    # ROZWIDLENIE: Zmiana planu vs Przedłużenie
    if breeder.current_plan and breeder.current_plan.name.lower() != plan.name.lower():
        # KLIENT ZMIENIŁ PLAN: Przeliczamy wartość starych dni na nowy czas
        remaining_value = remaining_days * old_daily_rate
        if new_daily_rate > 0:
            extra_days = int(remaining_value / new_daily_rate)
    else:
        # KLIENT PRZEDŁUŻA TEN SAM PLAN: Dodajemy po prostu jego stare dni
        extra_days = remaining_days

    # KROK 4: Zapis zaktualizowanego czasu
    breeder.current_plan = plan
    breeder.subscription_valid_until = now + timedelta(days=days_to_add + extra_days)
    breeder.save()

    # KROK 5: Kredyt Stripe (tylko manualne wpłaty BLIK/P24 przed odnowieniem karty)
    amount_total = getattr(session, "amount_total", 0)
    amount_pln = amount_total / 100.0 if amount_total else 0.0
    mode = getattr(session, "mode", "")

    if mode == "payment" and breeder.stripe_customer_id and amount_total > 0:
        try:
            stripe.Customer.create_balance_transaction(
                breeder.stripe_customer_id,
                amount=-int(
                    amount_total
                ),  # UWAGA: Minus w Stripe dodaje środki na rzecz klienta!
                currency="pln",
            )
        except Exception as e:
            print(f"⚠️ Błąd kredytu Stripe: {e}")

    # KROK 6: Zapis historii wpłat
    invoice_id = getattr(session, "invoice", None)
    invoice_url = ""
    if invoice_id:
        try:
            inv = stripe.Invoice.retrieve(invoice_id)
            invoice_url = getattr(inv, "hosted_invoice_url", "")
        except Exception:
            pass

    session_id = getattr(session, "id", "")
    try:
        Payment.objects.create(
            breeder=breeder,
            plan=plan,
            amount=amount_pln,
            payment_date=now,
            status=Payment.Status.COMPLETED,
            stripe_checkout_session_id=session_id,
            invoice_url=invoice_url,
        )
    except Exception as e:
        print(f"⚠️ Błąd zapisu w tabeli Payment: {e}")
