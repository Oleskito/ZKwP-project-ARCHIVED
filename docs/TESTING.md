# Testing

## Framework

This project uses **Django's built-in test framework** (`django.test`). The primary test runner is:

```bash
python manage.py test
```

`pytest` and `pytest-cov` are installed as alternatives but `manage.py test` is the authoritative runner. Use it for all CI and pre-commit checks.

For test coverage:

```bash
coverage run manage.py test
coverage report -m
```

## Test File Location

Each app has a `tests.py` file at its root. All three are currently empty — they are the starting point for all new tests.

```
accounts/tests.py
kennel/tests.py
billing/tests.py
```

When a single `tests.py` file grows beyond ~300 lines, convert it to a package:

```
kennel/
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    └── test_forms.py
```

## What to Test

### Models

Test `clean()` validation, `save()` side effects, `__str__` output, property methods, and DB constraint violations.

```python
from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.models import Breeder
from kennel.models import Dog


class DogModelTest(TestCase):
    def setUp(self):
        self.breeder = Breeder.objects.create_user(
            email="hodowca@example.com",
            password="testpass123",
            first_name="Jan",
            last_name="Kowalski",
        )

    def test_is_archived_true_when_status_is_sold(self):
        dog = Dog.objects.create(
            breeder=self.breeder,
            name="Reks",
            breeding_status=Dog.BreedingStatus.SOLD,
        )
        self.assertTrue(dog.is_archived)

    def test_is_archived_false_when_status_is_active(self):
        dog = Dog.objects.create(
            breeder=self.breeder,
            name="Reks",
            breeding_status=Dog.BreedingStatus.ACTIVE,
        )
        self.assertFalse(dog.is_archived)

    def test_father_must_be_male(self):
        female = Dog.objects.create(breeder=self.breeder, name="Luna", gender="female")
        dog = Dog(breeder=self.breeder, name="Reks", father=female)
        with self.assertRaises(ValidationError):
            dog.clean()
```

**Priority model tests:**
- `Dog.save()` — `is_archived` auto-set for every status value
- `Dog.clean()` — gender enforcement on father/mother
- `Litter.clean()` — mutual exclusivity of internal FK vs external snapshot
- `MedicalRecord.clean()` / `DocumentRecord.clean()` / `Measurement.clean()` — exactly one source
- `Payment.save()` — `amount` auto-fill from `plan.price`
- `Puppy.current_weight` / `current_height` — returns `None` when no measurements exist

### Views

Use `self.client` (Django's test client). Always set up a logged-in user in `setUp()`.

```python
from django.test import TestCase
from django.urls import reverse
from accounts.models import Breeder
from kennel.models import Dog


class DogViewTest(TestCase):
    def setUp(self):
        self.breeder = Breeder.objects.create_user(
            email="hodowca@example.com",
            password="testpass123",
        )
        self.other_breeder = Breeder.objects.create_user(
            email="other@example.com",
            password="testpass123",
        )
        self.client.login(email="hodowca@example.com", password="testpass123")

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard_dog"))
        self.assertRedirects(response, "/login/?next=/dashboard/dog/")

    def test_dog_list_only_shows_own_dogs(self):
        Dog.objects.create(breeder=self.breeder, name="Mój pies")
        Dog.objects.create(breeder=self.other_breeder, name="Cudzy pies")
        response = self.client.get(reverse("dashboard_dog"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mój pies")
        self.assertNotContains(response, "Cudzy pies")

    def test_cannot_edit_another_breeders_dog(self):
        dog = Dog.objects.create(breeder=self.other_breeder, name="Cudzy pies")
        response = self.client.get(reverse("dog_edit", args=[dog.pk]))
        self.assertEqual(response.status_code, 404)
```

**Key things to verify in every view test:**
1. Unauthenticated GET to any `/dashboard/*` URL returns a redirect to `/login/`
2. A breeder cannot GET or POST to another breeder's object URL (expect 404, not 403)
3. Valid POST form data redirects to the expected URL
4. Invalid POST form data re-renders the template with `form.errors` populated
5. Deletion via GET does not delete — only POST does

### Forms

Test form validation in isolation — no HTTP request needed.

```python
from django.test import TestCase
from kennel.forms import DogForm
from accounts.models import Breeder
import datetime


class DogFormTest(TestCase):
    def setUp(self):
        self.breeder = Breeder.objects.create_user(
            email="hodowca@example.com",
            password="testpass123",
        )

    def test_future_birth_date_is_invalid(self):
        form = DogForm(
            data={"name": "Reks", "birth_date": "2099-01-01"},
            breeder=self.breeder,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("birth_date", form.errors)

    def test_chip_number_must_be_15_digits(self):
        form = DogForm(
            data={"name": "Reks", "chip_number": "123"},
            breeder=self.breeder,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("chip_number", form.errors)
```

## Test Database

Django automatically creates a test database prefixed with `test_` and runs all tests in transactions that are rolled back between test cases. Test data never persists between tests and never touches the production database.

The test database uses the same engine as production (`DB_ENGINE` from `.env`), which means **PostgreSQL**. Never switch to SQLite for tests — PostgreSQL-specific behavior (constraints, JSON queries, `CheckConstraint`) must be tested against the real engine.

## No Fixtures

Do not use Django fixture files (`.json` or `.yaml`). They become stale and are hard to maintain. Use `setUp()` methods or helper factory functions instead:

```python
def make_dog(breeder, name="Testowy pies", **kwargs):
    return Dog.objects.create(breeder=breeder, name=name, **kwargs)
```

Keep factories in the test file itself — do not add a separate factories module unless multiple apps share them.

## Coverage Target

| App | Priority | Target |
|-----|----------|--------|
| `kennel` models | High | ≥ 80% |
| `kennel` views | High | ≥ 80% |
| `accounts` models / views | High | ≥ 80% |
| `billing` models | Medium | ≥ 60% (until views are implemented) |

Focus first on testing every code path in `save()`, `clean()`, and ownership-enforcement in views — these are the highest-risk areas.

## Running Specific Tests

```bash
# All tests
python manage.py test

# All tests in one app
python manage.py test accounts
python manage.py test kennel

# One test class
python manage.py test kennel.tests.DogModelTest

# One specific test method
python manage.py test kennel.tests.DogModelTest.test_is_archived_true_when_status_is_sold

# With verbose output
python manage.py test --verbosity=2

# Stop on first failure
python manage.py test --failfast
```