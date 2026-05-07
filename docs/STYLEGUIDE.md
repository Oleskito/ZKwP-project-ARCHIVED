# Style Guide

## Linting and Formatting

**Ruff** (`0.14.5`) is the sole linter and formatter for this project. It replaces `black`, standalone `isort`, and `pylint`. Do not run any other formatting tool.

```bash
ruff format .          # Format all Python files
ruff check .           # Lint all Python files
ruff check --fix .     # Lint and auto-fix all fixable issues
```

Always run both commands before committing any Python code.

### Ruff Configuration

There is currently no `pyproject.toml` in the project. When creating one, use this baseline:

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP"]
ignore = []

[tool.ruff.lint.isort]
known-first-party = ["accounts", "kennel", "billing"]
```

## Python Version

The project targets **Python 3.13**. Use modern syntax: `X | Y` union types, `match` statements where appropriate, built-in generics (`list[str]` not `List[str]`).

## General Conventions

- **Line length:** 100 characters maximum.
- **Indentation:** 4 spaces; no tabs.
- **String quotes:** Double quotes `"..."` for all strings. Ruff enforces consistency.
- **Trailing commas:** Use trailing commas in all multi-line collections, function signatures, and import groups to minimize diff noise.
- **Blank lines:** Two blank lines between top-level definitions; one blank line between methods.

## Import Order

Ruff's `isort` integration enforces the correct order automatically. The sections are:

```python
# 1. Standard library
import uuid
from pathlib import Path

# 2. Third-party
from django_countries.fields import CountryField
import encrypted_model_fields.fields as encrypted_fields

# 3. Django (part of third-party, but list Django imports together)
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

# 4. Local apps
from kennel.models import Dog
```

**Never use wildcard imports** (`from module import *`).

When referencing the custom user model in `ForeignKey` or `OneToOneField` definitions, **always use `settings.AUTH_USER_MODEL`** — never import `Breeder` directly from `accounts.models`.

## Models

### Template for new models

```python
import uuid

from django.conf import settings
from django.db import models


class MyModel(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Aktywny"
        INACTIVE = "inactive", "Nieaktywny"

    # PK and timestamps — always first, always in this order
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")

    # ForeignKeys
    breeder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Hodowca",
    )

    # Regular fields
    name = models.CharField(max_length=100, verbose_name="Nazwa")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,  # type: ignore
        verbose_name="Status",
    )

    class Meta:
        verbose_name = "Mój model"
        verbose_name_plural = "Moje modele"
        constraints = [
            models.UniqueConstraint(fields=["breeder", "name"], name="unique_name_per_breeder"),
        ]

    def __str__(self) -> str:
        return self.name
```

### Model rules

- **UUID PK and both timestamps are mandatory** on every new model — no exceptions.
- **`verbose_name` in Polish** on every field and in `class Meta`.
- **`TextChoices` as a nested inner class** for all choice fields. Pass `.choices` to the field and add `# type: ignore` if the type checker complains.
- **`on_delete` always explicit** — never rely on defaults. See `DATABASE.md` for the correct choice per relationship type.
- **`class Meta` before `__str__`** before other methods.
- **`__str__` always has a return type annotation** (`-> str`).
- **`clean()` for business logic, DB constraints for structural rules.** Purely structural invariants (e.g., "exactly one of these FKs must be set") belong in `class Meta: constraints`. Business rule validation (e.g., "father must be male") belongs in `clean()`.
- **`save()` must call `super().save(*args, **kwargs)`** and, when it calls `clean()`, must do so before `super().save()`. Keep `save()` minimal.
- **Properties for derived values** (`current_weight`, `current_height`) — do not add computed columns to the DB.

## Views

All views in `kennel/` are **function-based views (FBVs)**. Do not introduce class-based views without explicit discussion.

### Template

```python
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from kennel.models import Dog


@login_required
def dog_edit_view(request, pk):
    dog = get_object_or_404(Dog, pk=pk, breeder=request.user)

    if request.method == "POST":
        form = DogForm(request.POST, request.FILES, instance=dog)
        if form.is_valid():
            form.save()
            messages.success(request, "Dane psa zostały zapisane.")
            return redirect("dashboard_dog")
    else:
        form = DogForm(instance=dog)

    return render(request, "dashboard_dog/dashboard_dog_edit.html", {"form": form, "dog": dog})
```

### View rules

- **Always filter by `breeder=request.user`** — users must never be able to access another breeder's data. Use `get_object_or_404(Model, pk=pk, breeder=request.user)`, never just `get_object_or_404(Model, pk=pk)`.
- **Use `get_object_or_404`** — never use `.get(pk=pk)` without exception handling.
- **Redirect by URL name** — `redirect("dashboard_dog")`, not `redirect("/dashboard/dog/")`.
- **Use `messages.success()` / `messages.error()`** for user-facing feedback after POST actions.
- **Destructive actions (delete, status change) must verify `request.method == "POST"`** before executing. Render a confirmation page on GET.
- Never perform database writes in GET handlers.

## Forms

```python
from django import forms

from kennel.models import Dog


class DogForm(forms.ModelForm):
    class Meta:
        model = Dog
        fields = ["name", "gender", "breed", "birth_date"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder": "Imię psa",
            }),
        }
```

### Form rules

- **Apply Tailwind classes via `attrs={"class": "..."}`** in widget definitions. Never use `<style>` blocks or inline `style=` attributes.
- **`validate_<field>()` methods** for custom field validation. Keep them focused on one rule.
- **`clean()` on the form** for cross-field validation.
- **Set `form.instance.breeder = request.user`** before `form.save(commit=False)` whenever the form does not expose the `breeder` field.
- **Filter querysets in `__init__`** when form fields reference model objects that must be scoped to the current user:

```python
def __init__(self, *args, breeder=None, **kwargs):
    super().__init__(*args, **kwargs)
    if breeder:
        self.fields["litter"].queryset = Litter.objects.filter(breeder=breeder)
```

## Templates

- **Always extend a base template** — `{% extends "dashboard/kennel_panel_base.html" %}` or `{% extends "home_pages/public_base.html" %}`.
- **`{% load static %}`** at the top of any template that references static files.
- **`{% url 'name' %}`** for all internal links — never hardcode URL paths.
- **`{% csrf_token %}`** inside every `<form>` that uses `method="post"`.
- **All user-visible text is in Polish.**
- **No `<style>` blocks** in individual page templates. Custom CSS belongs only in base templates or `Styles/input.css`.
- **No inline `style=` attributes** — use Tailwind utility classes exclusively.
- Template file names follow the pattern defined in `ARCHITECTURE.md`.

## Type Annotations

Use type hints on all function signatures and return values. For Django views, annotate the return type as `HttpResponse`:

```python
from django.http import HttpResponse

@login_required
def dashboard_view(request) -> HttpResponse:
    ...
```

For model methods and properties:

```python
def __str__(self) -> str:
    return self.name

@property
def current_weight(self) -> float | None:
    measurement = self.measurement_set.filter(weight__isnull=False).first()
    return measurement.weight if measurement else None
```

For utility functions:

```python
def verify_turnstile(token: str) -> bool:
    ...
```

## Security Rules

- **No hardcoded secrets.** Every API key, database credential, and encryption key comes from `os.getenv(...)` via `python-dotenv`. If `os.getenv(...)` returns `None` for a required key, the application should fail loudly at startup.
- **Never log sensitive data.** Buyer ID numbers, raw passwords, payment details, and encryption keys must never appear in log output.
- **Always use `{% csrf_token %}`** in every POST form.
- **Validate ownership in every view** that retrieves an object by PK — always include `breeder=request.user` in the queryset filter.
- **No raw SQL.** Use the Django ORM. `Manager.raw()` and `connection.cursor()` are forbidden without documented justification.
- **No `DEBUG=True` in production.** The `ALLOWED_HOSTS` list must be set before deployment.
- **`is_archived` on `Dog` is managed by `Dog.save()` only.** Never set it directly in views or forms.