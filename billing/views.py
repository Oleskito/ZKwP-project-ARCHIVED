import logging

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

    try:
        if is_topup:
            plan_key = PRICE_ID_TO_PLAN.get(price_id)
            if not plan_key:
                raise ValueError(f"Brak mapowania planu dla price_id: {price_id}")
            plan_name, interval = plan_key
            plan = SubscriptionPlan.objects.get(name=plan_name, interval=interval)
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=[{
                    "quantity": 1,
                    "price_data": {
                        "currency": "pln",
                        "unit_amount": int(plan.price * 100),
                        "product_data": {"name": f"Plan {plan.name} – Doładowanie"},
                    },
                }],
                client_reference_id=str(request.user.id),
                locale="pl",
                metadata={"price_id": price_id, "checkout_type": "topup"},
                success_url=request.build_absolute_uri("/billing/success/"),
                cancel_url=request.build_absolute_uri("/billing/cancel/"),
            )
        else:
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                client_reference_id=str(request.user.id),
                locale="pl",
                metadata={"price_id": price_id},
                success_url=request.build_absolute_uri("/billing/success/"),
                cancel_url=request.build_absolute_uri("/billing/cancel/"),
            )
    except Exception:
        logger.exception("Stripe checkout session creation failed for user %s", request.user.id)
        messages.error(
            request, "Wystąpił błąd przy przetwarzaniu płatności. Spróbuj ponownie."
        )
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
        messages.error(request, "Nie można otworzyć portalu zarządzania. Spróbuj ponownie.")
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

    print("--- KROK 1: SZUKAM UZYTKOWNIKA ---")
    user_id = getattr(session, 'client_reference_id', None)
    print(f"👉 user_id z kasy Stripe: {user_id}")
    if not user_id:
        print("❌ PRZERWANO: Stripe nie przesłał ID użytkownika (client_reference_id)!")
        return

    User = get_user_model()
    try:
        breeder = User.objects.get(id=user_id)
        print(f"👉 Znaleziono hodowce w bazie: {breeder.email}")
    except User.DoesNotExist:
        print("❌ PRZERWANO: Hodowca o tym ID nie istnieje w bazie danych!")
        return

    print("--- KROK 2: AKTUALIZACJA ID STRIPE ---")
    customer_id = getattr(session, 'customer', None)
    subscription_id = getattr(session, 'subscription', None)
    print(f"👉 customer_id: {customer_id}, subscription_id: {subscription_id}")

    stripe_fields = []
    if not breeder.stripe_customer_id and customer_id:
        breeder.stripe_customer_id = customer_id
        stripe_fields.append("stripe_customer_id")
    if not breeder.stripe_subscription_id and subscription_id:
        breeder.stripe_subscription_id = subscription_id
        stripe_fields.append("stripe_subscription_id")

    if stripe_fields:
        breeder.save(update_fields=stripe_fields)
        print("👉 Zapisano klucze Stripe do profilu użytkownika.")

    print("--- KROK 3: ODCZYT PLANU Z METADANYCH ---")
    metadata = getattr(session, 'metadata', None)

    # Próba wyciągnięcia price_id (kompatybilność z nowym i starym Stripe)
    price_id = getattr(metadata, 'price_id', "") if metadata else ""
    if not price_id and hasattr(metadata, 'get'):
        price_id = metadata.get('price_id', "")

    print(f"👉 price_id odczytane z kasy: '{price_id}'")

    plan_key = PRICE_ID_TO_PLAN.get(price_id)
    print(f"👉 Klucz planu ze słownika Django: {plan_key}")
    if not plan_key:
        print("❌ PRZERWANO: Cennik Django nie rozpoznaje tego price_id!")
        return

    plan_name, interval = plan_key
    try:
        plan = SubscriptionPlan.objects.get(name=plan_name, interval=interval)
        print(f"👉 Zidentyfikowano plan: {plan.name} ({plan.interval})")
    except SubscriptionPlan.DoesNotExist:
        print("❌ PRZERWANO: Ten plan nie jest utworzony w panelu Administratora (bazie danych)!")
        return

    print("--- KROK 4: AKTUALIZACJA SUBSKRYPCJI ---")
    if breeder.current_plan_id != plan.pk:
        breeder.current_plan = plan
        breeder.save(update_fields=["current_plan"])
        print("👉 Zaktualizowano bieżący plan użytkownika.")

    mode = getattr(session, 'mode', 'nieznany')
    months = 12 if interval == "yearly" else 1
    breeder.extend_subscription(months=months)
    breeder.save()

    print(f"👉 Aktywowano/przedłużono subskrypcję o {months} miesięcy (tryb: {mode}).")

    print("--- KROK 5: ZAPIS DO TABELI PŁATNOŚCI ---")
    amount_total = getattr(session, 'amount_total', 0)
    amount_pln = amount_total / 100.0 if amount_total else 0.0
    print(f"👉 Kwota do zapisu: {amount_pln} PLN")

    invoice_id = getattr(session, 'invoice', None)
    invoice_url = ""
    if invoice_id:
        try:
            import stripe
            inv = stripe.Invoice.retrieve(invoice_id)
            invoice_url = getattr(inv, 'hosted_invoice_url', "")
            print("👉 Pobrano link do faktury.")
        except Exception as e:
            print(f"⚠️ Uwaga: Nie udało się pobrać faktury: {e}")

    session_id = getattr(session, 'id', "")

    try:
        Payment.objects.create(
            breeder=breeder,
            plan=plan,
            amount=amount_pln,
            payment_date=timezone.now(),
            status=Payment.Status.COMPLETED,
            stripe_checkout_session_id=session_id,
            invoice_url=invoice_url,
        )
        print("✅ SUKCES! Utworzono nowy rekord w tabeli Płatności!")
    except Exception as e:
        print(f"❌ KRYTYCZNY BLAD PRZY ZAPISIE REKORDU DO BAZY: {e}")
        import traceback
        traceback.print_exc()