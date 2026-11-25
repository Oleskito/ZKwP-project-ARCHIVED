<div align="center">

# 🐾 Przydomek.pl

### Nowoczesna Platforma SaaS do Kompleksowego Zarządzania Hodowlą Psów Rasowych (ZKwP / FCI)

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Stripe](https://img.shields.io/badge/Stripe-API-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://stripe.com/)
[![Cloudflare Turnstile](https://img.shields.io/badge/Cloudflare-Turnstile-F38020?style=for-the-badge&logo=cloudflare&logoColor=white)](https://www.cloudflare.com/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black?style=for-the-badge)](https://github.com/astral-sh/ruff)

<p align="center">
  <b>Cyfrowy asystent hodowcy: ewidencja stada, drzewa genealogiczne, kontrola miotów, biometria szczeniąt, szyfrowana baza nabywców oraz zintegrowane płatności Stripe (BLIK / P24 / Karta).</b>
</p>

</div>

---

## 📖 O Projekcie

**Przydomek.pl** to produkcyjna aplikacja internetowa w architekturze SaaS stworzona specjalnie dla hodowców psów rasowych zrzeszonych w **Związku Kynologicznym w Polsce (ZKwP)** – jedynej polskiej organizacji należącej do międzynarodowej federacji **FCI (Fédération Cynologique Internationale)**.

Prowadzenie profesjonalnej hodowli wiąże się ze skomplikowaną biurokracją: restrykcyjnymi regulaminami hodowlanymi, terminowością zgłoszeń, ewidencją zabiegów weterynaryjnych, badaniami DNA, kontrolą miotów oraz rozliczeniami podatkowymi. **Przydomek.pl** centralizuje te procesy w jednym intuicyjnym, responsywnym i bezpiecznym panelu hodowcy.

> 💡 **Projekt stworzony jako demonstracja umiejętności fullstackowych**: dojrzałej architektury backendu w Django/PostgreSQL, bezpieczeństwa danych osobowych (PII), integracji płatności subskrypcyjnych Stripe, nowoczesnego frontendu TailwindCSS oraz rygorystycznych standardów czystego kodu.

---

## 🗺️ Mapa Projektu i Dokumentacja Modułowa

Projekt został zaprojektowany w sposób wysoce modułowy, ze szczegółową dokumentacją techniczną każdego komponentu. Kliknij poniższe odnośniki, aby przejść do dedykowanych przewodników:

| Moduł / Dokument | Rola i Zakres |
|:---|:---|
| 🐶 [**`kennel/` – Moduł Hodowli**](kennel/README.md) | Kartoteki psów dorosłych, mioty, szczenięta, promocja szczeniąt, biometria, historia medyczna, dokumenty i szyfrowana baza nabywców. |
| 🔐 [**`accounts/` – Uwierzytelnianie & Użytkownicy**](accounts/README.md) | Dedykowany model `Breeder` (bez username), ochrona Cloudflare Turnstile, obsługa sesji 30-dniowych oraz zaawansowana maszyna stanów subskrypcji. |
| 💳 [**`billing/` – Płatności & Monetyzacja SaaS**](billing/README.md) | Integracja ze Stripe (Checkout, Webhooks, Customer Portal), obsługa kart, **BLIK-a** i **Przelewów24**, cykle miesięczne/roczne i faktury PDF. |
| 📚 [**`docs/` – Centrum Wiedzy Architektonicznej**](docs/README.md) | Spis wytycznych technicznych i wzorców projektowych. |
| 🏛️ [**`docs/ARCHITECTURE.md`**](docs/ARCHITECTURE.md) | Routing bez per-app URLs, wzorzec szablonów, integracja Tailwind CSS v4, vanilla JS, polityka CSP. |
| 🗄️ [**`docs/DATABASE.md`**](docs/DATABASE.md) | Schemat bazy PostgreSQL, reguły UUIDv4 i timestampów, referencja modeli, ograniczenia CheckConstraint, reguły ciągłości subskrypcji. |
| 🧪 [**`docs/TESTING.md`**](docs/TESTING.md) | Środowisko testowe Django, testy modeli, widoków i formularzy, izolacja danych PostgreSQL. |
| 🎨 [**`docs/STYLEGUIDE.md`**](docs/STYLEGUIDE.md) | Reguły Ruff (linter/formatter), standardy Python 3.13, wytyczne typowania (Type Hints) i wzorce FBV. |

---

## ✨ Kluczowe Funkcjonalności

### 🐕 1. Ewidencja Stada Hodowlanego & Genealogia
- Rejestracja suk hodowlanych i reproduktorów z uwzględnieniem numerów **PKR** (Polska Księga Rodowodowa), numerów rejestracji oddziałowej ZKwP, chipów i tatuaży.
- Samoreferencyjne drzewo genealogiczne (`father`, `mother`).
- Automatyczne archiwizowanie wycofanych ze stada psów na poziomie metody `save()`.
- Obsługa współwłasności psów z pełnymi danymi współwłaściciela.

### 🍼 2. Zarządzanie Miotami i Cyklem Rozrodu
- Śledzenie pełnego cyklu życia miotu: *Planowany ➔ Krycie ➔ Pusty / Narodziny ➔ Zgłoszony ➔ Po Przeglądzie ➔ Zarchiwizowany*.
- **Wzorzec zewnętrznego reproduktora**: jeśli ojciec/matka należy do zewnętrznej hodowli, dane przechowywane są w migawce JSON (`father_data_snapshot`), zwalniając z konieczności tworzenia fikcyjnego profilu psa w bazie.
- Wzajemne wykluczenie powiązania kluczem obcym i migawki JSON egzekwowane na poziomie walidacji `clean()`.

### 🚀 3. Wzorzec Promocji Szczenięcia (`Puppy Promotion`)
- Szczenię pozostające w hodowli jednym kliknięciem może zostać przekształcone w dorosły profil `Dog`.
- Relacja `OneToOneField` zachowuje pełną historię wczesnodziecięcą psa (pomiary, wagę, szczepienia).
- Blokada edycji zduplikowanych pól tożsamościowych chroni przed niespójnościami danych.

### 📈 4. Dziennik Rozwoju i Pomiary Biometryczne
- Regularna rejestracja parametrów fizycznych: waga (kg), wysokość w kłębie (cm), obwód klatki piersiowej, obwód głowy, długość ciała, temperatura oraz ocena kondycji **BCS (Body Condition Score 1–9)**.
- Rejestr fotograficzny zmian sylwetki.
- Dynamiczne właściwości `current_weight` oraz `current_height` wyciągające najświeższy wpis z osi czasu.

### 🩺 5. Kartoteka Medyczna i Elektroniczne Archiwum Dokumentów
- Polimorficzne powiązanie wpisów: szczepienie, badanie lub certyfikat może dotyczyć pojedynczego psa, konkretnego szczeniaka lub całego miotu (np. zbiorcze odrobaczenie).
- Integralność bazy danych zabezpieczona więzami `CheckConstraint` (dokładnie jedno źródło zwierzęce).
- Słowniki zabiegów i wyników połączone kaskadowo przez `django-smart-selects`.

### 👤 6. Szyfrowana Kartoteka Nabywców
- Bezpieczny rejestr rezerwacji i umów sprzedaży szczeniąt.
- **Kryptograficzne szyfrowanie numerów PESEL i dowodów osobistych** w spoczynku (At-Rest Encryption) za pomocą biblioteki `django-encrypted-model-fields` (Fernet).

### 💳 7. Monetyzacja SaaS i Płatności Stripe
- Trzy poziomy abonamentowe: **Start**, **Pro**, **VIP** z limitami psów i miotów.
- Dostępne cykle: miesięczny oraz roczny.
- Obsługa płatności popularnych na polskim rynku: **karty kredytowe**, **BLIK** oraz **Przelewy24**.
- Bezpieczny webhook Stripe (`checkout.session.completed`) automatycznie aktywujący i przedłużający abonament.
- Samodzielny portal klienta **Stripe Billing Customer Portal** umożliwiający pobieranie faktur i zarządzanie kartami.
- 2-miesięczny darmowy okres próbny dla nowych hodowców.

---

## 🔒 Architektura Bezpieczeństwa (Security by Design)

Projekt kładzie szczególny nacisk na bezpieczeństwo danych i prywatność użytkowników:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        WARSTWY BEZPIECZEŃSTWA                          │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Ochrona Brute-Force & Botów : Cloudflare Turnstile CAPTCHA          │
│ 2. Bezpieczeństwo HTTP Headers : django-csp (Strict Content-Security)  │
│ 3. Izolacja Danych (Multi-Tenancy): Breeder Scoping (breeder=user)     │
│ 4. Ochrona Danych Osobowych    : Szyfrowanie Fernet (PESEL / Dowód)    │
│ 5. Płatności i Webhooks        : PCI-DSS Compliance via Stripe         │
│ 6. Zarządzanie Sekretami       : 100% .env (Brak sekretów w repozytorium)│
└────────────────────────────────────────────────────────────────────────┘
```

1. **Izolacja danych najemców (Tenant Scoping)**: Każdy widok w `kennel/views.py` jawnie weryfikuje własność zasobów (`get_object_or_404(Model, pk=pk, breeder=request.user)`). Użytkownik nie ma możliwości podglądu ani edycji cudzego psa, miotu czy dokumentu.
2. **Kryptograficzne szyfrowanie pól (Field-Level Encryption)**: Wrażliwe dane nabywców (`Buyer.id_number`) są szyfrowane kluczem Fernet (AES-128-CBC + HMAC) przed zapisem do PostgreSQL.
3. **Podpisy cyfrowe Stripe Webhook**: Wszystkie zdarzenia przychodzące ze Stripe są weryfikowane kryptograficznie (`stripe.Webhook.construct_event`) za pomocą dedykowanego sekretu.
4. **Content Security Policy (CSP)**: Nagłówki CSP blokują możliwość wstrzyknięcia nieautoryzowanych skryptów (ochrona przed XSS).
5. **Turnstile CAPTCHA**: Formularze logowania i rejestracji są chronione przez niewidzialny token Cloudflare Turnstile, walidowany po stronie serwera przed rozpoczęciem autentykacji.

---

## 🛠️ Stos Technologiczny

| Kategoria | Technologia | Wersja | Zastosowanie |
|:---|:---|:---|:---|
| **Język** | Python | `3.13` | Nowoczesna składnia, unie typów `X \| Y`, pattern matching |
| **Framework** | Django | `6.0` | Główny framework MVC/MVT, ORM, autentykacja, migracje |
| **Baza Danych** | PostgreSQL | `16+` | Relacyjna baza danych, więzy integralności, JSONB |
| **Frontend** | HTML5 / Vanilla JS | ES6+ | Lekki, czysty kod bez ciężkich frameworków SPA |
| **Styling** | Tailwind CSS | `v4` | Nowoczesny silnik CSS, modułowy utility-first design |
| **Płatności** | Stripe API | `2026-04-22.dahlia` | Checkout Sessions, Customer Portal, Webhooki, BLIK, P24 |
| **Kryptografia** | Cryptography / Fernet | `46+` | Szyfrowanie danych osobowych (PII) w bazie |
| **Bezpieczeństwo** | Cloudflare Turnstile | v1 | Niewidzialna ochrona przed botami i atakami słownikowymi |
| **Jakość Kodu** | Ruff | `0.14+` | Błyskawiczny linter i formatter kodu Python |
| **Środowisko** | python-dotenv | `1.2+` | Wstrzykiwanie zmiennych środowiskowych z pliku `.env` |

---

## 🚀 Szybki Start (Instalacja i Uruchomienie)

### Wymagania Wstępne
- **Python 3.13+**
- **PostgreSQL 14+**
- Menedżer pakietów **pip**

### 1. Klonowanie repozytorium
```bash
git clone git@github.com:Oleskito/ZKwP-project.git
cd ZKwP-project
```

### 2. Utworzenie środowiska wirtualnego
```bash
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Linux / macOS:
source .venv/bin/activate
```

### 3. Instalacja zależności
```bash
pip install -r requirements.txt
```

### 4. Konfiguracja zmiennych środowiskowych
Skopiuj szablon konfiguracji `.env.example` do pliku `.env`:
```bash
cp .env.example .env
```
Otwórz `.env` w edytorze i skonfiguruj parametry bazy PostgreSQL oraz klucze API:
```env
SECRET_KEY="twoj-unikalny-tajny-klucz-django"
DEBUG=True

DB_ENGINE=django.db.backends.postgresql
DB_NAME=project_db
DB_USER=postgres
DB_PASSWORD=twoje_haslo_bazy
DB_HOST=localhost
DB_PORT=5432

# Wygeneruj w Pythonie:
# python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
FIELD_ENCRYPTION_KEY="twoj-klucz-fernet="

TURNSTILE_SECRET_KEY="twoj-klucz-turnstile"
STRIPE_PUBLIC_KEY="pk_test_..."
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
```

### 5. Przygotowanie bazy danych (Migracje)
```bash
# Upewnij się, że baza danych PostgreSQL o nazwie 'project_db' istnieje
python manage.py migrate
```

### 6. Utworzenie konta administratora
```bash
python manage.py createsuperuser
```

### 7. Uruchomienie serwera deweloperskiego
```bash
python manage.py runserver
```
Aplikacja dostępna będzie pod adresem: **http://127.0.0.1:8000/**  
Panel administratora: **http://127.0.0.1:8000/admin/**

---

## 🧪 Testy & Jakość Kodu

W projekcie wykorzystywany jest wbudowany test runner Django oparty na `unittest`, a także narzędzie **Ruff** odpowiadające za bezkompromisową czystość kodu:

```bash
# Uruchomienie wszystkich testów automatycznych
python manage.py test

# Testy konkretnego modułu
python manage.py test accounts
python manage.py test kennel
python manage.py test billing

# Formatowanie kodu za pomocą Ruff
ruff format .

# Sprawdzenie i automatyczna naprawa ostrzeżeń lintera
ruff check --fix .
```

---

## 📁 Struktura Katalogów

```
Projekt ZKwP/
├── core_config/          # Konfiguracja nadrzędna Django (settings, urls, wsgi/asgi)
├── accounts/             # Moduł użytkowników, autentykacja, Breeder model
│   └── README.md         # Dokumentacja modułu accounts
├── kennel/               # Główny moduł biznesowy: psy, mioty, szczenięta, badania
│   └── README.md         # Dokumentacja modułu kennel
├── billing/              # Moduł rozliczeń, subskrypcje, Stripe Checkout & Webhooki
│   └── README.md         # Dokumentacja modułu billing
├── templates/            # Szablony HTML (public_base, panel_base, partials)
├── docs/                 # Szczegółowa dokumentacja techniczna
│   ├── README.md         # Hub dokumentacji
│   ├── ARCHITECTURE.md   # Architektura oprogramowania
│   ├── DATABASE.md       # Projekt bazy danych i specyfikacja pól
│   ├── STYLEGUIDE.md     # Standardy kodowania i czystego kodu
│   └── TESTING.md        # Strategia testowania
├── Styles/               # Style Tailwind CSS (input.css, output.css)
├── Static/               # Zasoby statyczne (AOS, logo, ikony)
├── media/                # Katalog załączników użytkowników (.gitkeep)
├── .env.example          # Wzorzec bezpiecznej konfiguracji środowiskowej
├── .gitignore            # Rygorystyczne wykluczenia sekretów i plików roboczych
├── manage.py             # Narzędzie CLI Django
└── requirements.txt      # Zależności produkcyjne projektu
```

---

## 👨‍💻 Autor & Kontakt

Projekt zrealizowany przez **Aleksandra Ostrycharza** jako nowoczesne narzędzie SaaS dla polskiej kynologii.

- **GitHub**: [@Oleskito](https://github.com/Oleskito)
- **Email**: [olekpatrykostrycharz@gmail.com](mailto:olekpatrykostrycharz@gmail.com)
- **Projekt**: Przydomek.pl – System Zarządzania Hodowlą ZKwP

---

<div align="center">
  <sub>Zaprojektowano z dbałością o architekturę, czysty kod i bezpieczeństwo danych.</sub>
</div>
