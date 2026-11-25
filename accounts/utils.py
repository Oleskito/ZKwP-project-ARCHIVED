import requests
from django.conf import settings


def verify_turnstile(request):
    """
    Sprawdza token Cloudflare Turnstile z bezpiecznym limitem czasu (timeout).
    Zwraca True, jeśli weryfikacja przebiegła pomyślnie, w przeciwnym razie False.
    """
    turnstile_token = request.POST.get("cf-turnstile-response")
    if not turnstile_token:
        return False

    verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {"secret": settings.TURNSTILE_SECRET_KEY, "response": turnstile_token}

    try:
        # KRYTYCZNE: timeout=5 chroni serwer przed zawieszeniem
        response = requests.post(verify_url, data=data, timeout=5)
        outcome = response.json()
        return outcome.get("success", False)
    except Exception as e:
        print(f"Błąd połączenia z Cloudflare: {e}")
        return False
