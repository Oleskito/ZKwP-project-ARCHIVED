# 📚 Dokumentacja Techniczna Projektu (`docs/`)

Katalog zawiera szczegółową dokumentację techniczną, standardy projektowe, specyfikację modeli danych oraz wytyczne testowania aplikacji **Przydomek.pl**.

---

## 📑 Spis Dokumentów

| Dokument | Tematyka | Główne zagadnienia |
|----------|----------|-------------------|
| 🏛️ [**ARCHITECTURE.md**](ARCHITECTURE.md) | **Architektura Systemu** | Struktura aplikacji Django, routing bez per-app urls, szablony, Tailwind CSS v4 pipeline, architektura JS, mechanizmy bezpieczeństwa (CSP, Turnstile, CSRF, izolacja danych). |
| 🗄️ [**DATABASE.md**](DATABASE.md) | **Baza Danych & Modele** | Reguły PostgreSQL (UUID PK, timestamps), pełna referencja pól modeli we wszystkich aplikacjach, cykl życia subskrypcji, reguła ciągłości, ograniczenia CheckConstraint. |
| 🧪 [**TESTING.md**](TESTING.md) | **Strategia Testów** | Konfiguracja test runnera Django, architektura testów jednostkowych i integracyjnych, testowanie modeli, widoków, formularzy, testowa baza PostgreSQL. |
| 🎨 [**STYLEGUIDE.md**](STYLEGUIDE.md) | **Standardy Kodu** | Reguły Ruff (linter i formatter), standardy Python 3.13, wzorce projektowe modeli, widoków FBV i formularzy, konwencje typowania, zasady bezpieczeństwa. |

---

## 🎯 Zasady Pracy z Projektem (Dispatcher Pattern)

Wszystkie modyfikacje logiki biznesowej, modeli i interfejsu powinny być weryfikowane z powyższą dokumentacją:
- Przed zmianą schematu bazy danych ➡️ sprawdź [DATABASE.md](DATABASE.md).
- Przed dodawaniem widoków lub komponentów UI ➡️ sprawdź [ARCHITECTURE.md](ARCHITECTURE.md) oraz [STYLEGUIDE.md](STYLEGUIDE.md).
- Przed pisaniem testów ➡️ sprawdź [TESTING.md](TESTING.md).

---

## 🔗 Nawigacja
- ⬅️ [Wróć do głównego README](../README.md)
- 🔐 [Moduł Kont (`accounts/`)](../accounts/README.md)
- 🐶 [Moduł Hodowli (`kennel/`)](../kennel/README.md)
- 💳 [Moduł Płatności (`billing/`)](../billing/README.md)
