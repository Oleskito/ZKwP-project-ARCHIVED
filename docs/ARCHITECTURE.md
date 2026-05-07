# Architecture

## Project Overview

**Przydomek.pl** is a SaaS web application for Polish dog breeders registered with ZKwP (Związek Kynologiczny w Polsce). It centralizes kennel management: tracking dogs, litters, puppies, health measurements, medical records, and documents, with subscription-based access control.

## Django App Structure

```
core_config/    # Project configuration — settings, URLs, WSGI/ASGI
accounts/       # Custom user model (Breeder), authentication, registration
kennel/         # Core domain — dogs, litters, puppies, measurements, medical/document records
billing/        # Subscription plans and payment records
templates/      # All HTML templates (single top-level directory, no per-app templates)
Styles/         # Tailwind CSS source (input.css) and compiled output (output.css)
Static/         # Static assets (AOS.js, AOS.css, logos)
media/          # User-uploaded files (dog photos, litter covers, measurement photos)
```

### `core_config/`

Central Django configuration. There are no per-app `urls.py` files — all routing is in `core_config/urls.py`.

| File | Role |
|------|------|
| `settings.py` | All project settings — database via env vars, installed apps, CSP headers, media/static paths |
| `urls.py` | Single root URLconf for the entire project |
| `wsgi.py` / `asgi.py` | Deployment entrypoints |

**Critical settings:**
- `AUTH_USER_MODEL = "accounts.Breeder"` — custom user model; never change after initial migration
- `LANGUAGE_CODE = "pl"` / `TIME_ZONE = "Europe/Warsaw"` — fully Polish-localized
- `SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `TURNSTILE_SECRET_KEY` — always from environment variables, never hardcoded
- `CSP_*` directives configured for production security

### `accounts/`

Handles user identity and authentication. `Breeder` extends `AbstractUser` and is the project's sole user model.

**Key rules:**
- `username` is removed; `email` is the `USERNAME_FIELD`
- Never import `Breeder` directly for ForeignKey definitions — always use `settings.AUTH_USER_MODEL`
- `login_view` and `register_view` verify a Cloudflare Turnstile token via `accounts/utils.py:verify_turnstile()` before processing
- Logout uses Django's built-in `LogoutView`

### `kennel/`

The core domain app. All views are `@login_required` and function-based (FBVs). Never introduce class-based views without explicit discussion.

**Domain objects:**

| Model | Description |
|-------|-------------|
| `Dog` | Registered adult dogs; self-referential parent links (father/mother) |
| `Breed` | Breed reference data; managed exclusively via admin |
| `Litter` | Breeding event; links mother + father (internal FK or external JSON snapshot) |
| `Puppy` | Puppy within a litter; can be promoted to a full `Dog` record |
| `Buyer` | Buyer contact data with encrypted ID/PESEL number |
| `Measurement` | Time-series physical measurements (weight, height, BCS, etc.) for dogs or puppies |
| `MedicalRecord` | Medical events linked to a dog, puppy, or litter |
| `DocumentRecord` | Document metadata linked to a dog, puppy, or litter |
| `TreatmentType` / `TreatmentResult` | Lookup tables chained via `django-smart-selects` |

**Puppy promotion pattern:**
A puppy that stays in the kennel can be "promoted" to an adult `Dog` profile. `Puppy.adult_dog_profile` (`OneToOneField`) stores the link. Promotion can be reversed when the dog is deleted, restoring the original puppy record. Views actively protect promoted puppies from edits that would break this relationship (chip, tattoo, gender, name, color are locked).

**External parent pattern:**
If a litter's mother or father belongs to another kennel, their data is stored in `father_data_snapshot` / `mother_data_snapshot` (JSONField). A `Litter` cannot simultaneously hold both an internal FK and an external snapshot for the same parent — enforced via `clean()` called from `save()`.

**Polymorphic records:**
`MedicalRecord`, `DocumentRecord`, and `Measurement` each link to exactly one of `dog`, `puppy`, or `litter` via nullable ForeignKeys. This is enforced at both the DB level (`CheckConstraint`) and the model level (`clean()`).

### `billing/`

Minimal — models and admin only; no views yet.

- `SubscriptionPlan` — plan name, price, duration in days
- `Payment` — payment record linked to a `Breeder` and `SubscriptionPlan`; `amount` is auto-filled from `plan.price` on creation if not explicitly provided

## URL Routing

All routes are defined in `core_config/urls.py`. All `<uuid:pk>` segments use Django's UUID path converter.

| Pattern | Name | Handler |
|---------|------|---------|
| `/` | `home` | `account_views.home_view` |
| `/login/` | `login` | `account_views.login_view` |
| `/logout/` | `logout` | Django `LogoutView` |
| `/register/` | `register` | `account_views.register_view` |
| `/price_list/` | `price_list` | `account_views.price_list_view` |
| `/chaining/` | — | `smart_selects.urls` |
| `/dashboard/` | `dashboard` | `kennel_views.dashboard_view` |
| `/dashboard/dog/` | `dashboard_dog` | `kennel_views.dashboard_dog_view` |
| `/dashboard/dog/add/` | `dog_add` | `kennel_views.dog_add_view` |
| `/dashboard/dog/<uuid:pk>/edit/` | `dog_edit` | `kennel_views.dog_edit_view` |
| `/dashboard/dog/<uuid:pk>/delete/` | `dog_delete` | `kennel_views.dog_delete_view` |
| `/dashboard/dog/<uuid:pk>/measurements/` | `dog_measurements` | `kennel_views.dog_measurements_view` |
| `/dashboard/litter/` | `dashboard_litter` | `kennel_views.dashboard_litter_view` |
| `/dashboard/litter/add/` | `litter_add` | `kennel_views.litter_add_view` |
| `/dashboard/litter/<uuid:pk>/edit/` | `litter_edit` | `kennel_views.litter_edit_view` |
| `/dashboard/litter/<uuid:pk>/delete/` | `litter_delete` | `kennel_views.litter_delete_view` |
| `/dashboard/puppy/` | `dashboard_puppy` | `kennel_views.dashboard_puppy_view` |
| `/dashboard/puppy/add/` | `puppy_add` | `kennel_views.puppy_add_view` |
| `/dashboard/puppy/<uuid:pk>/edit/` | `puppy_edit` | `kennel_views.puppy_edit_view` |
| `/dashboard/puppy/<uuid:pk>/delete/` | `puppy_delete` | `kennel_views.puppy_delete_view` |
| `/dashboard/puppy/<uuid:pk>/measurements/` | `puppy_measurements` | `kennel_views.puppy_measurements_view` |
| `/dashboard/measurement/<uuid:pk>/edit/` | `measurement_edit` | `kennel_views.measurement_edit_view` |
| `/dashboard/measurement/<uuid:pk>/delete/` | `measurement_delete` | `kennel_views.measurement_delete_view` |

## Template Architecture

All templates live in the top-level `templates/` directory. There are two base templates:

| Base template | Used by |
|---------------|---------|
| `templates/home_pages/public_base.html` | All public-facing pages (home, login, register, price list) |
| `templates/dashboard/kennel_panel_base.html` | All authenticated dashboard pages |

**Directory layout:**

```
templates/
├── home_pages/
│   ├── public_base.html
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   └── price_list.html
├── dashboard/
│   ├── kennel_panel_base.html
│   ├── dashboard.html
│   └── measurement_edit.html
├── dashboard_dog/
│   ├── dashboard_dog.html              # List with tabs and filters
│   ├── dashboard_dog_add.html
│   ├── dashboard_dog_edit.html
│   ├── dashboard_dog_confirm_delete.html
│   ├── dashboard_dog_accordion_row.html  # Reusable list item partial
│   └── dashboard_dog_measurements.html
├── dashboard_litter/                   # Same pattern as above
└── dashboard_puppy/                    # Same pattern as above
```

Each entity section follows this naming convention:
- `dashboard_{entity}.html` — filterable list with tabs
- `dashboard_{entity}_add.html` — create form
- `dashboard_{entity}_edit.html` — edit form
- `dashboard_{entity}_confirm_delete.html` — delete confirmation page
- `dashboard_{entity}_accordion_row.html` — reusable accordion/list item partial
- `dashboard_{entity}_measurements.html` — measurement list + inline add form

## TailwindCSS Integration

The project uses **Tailwind CSS v4**.

- **Source:** `Styles/input.css` — Tailwind directives, Poppins font import, custom scrollbar styles
- **Compiled output:** `Styles/output.css` — generated by `tailwindcss.exe`; ignored by git and `.claudeignore`
- Both `Styles/` and `Static/` are listed in `STATICFILES_DIRS`

**Current loading strategy (important distinction):**

| Section | How Tailwind is loaded |
|---------|------------------------|
| Public pages (`public_base.html`) | Compiled `output.css` via `{% static %}` |
| Dashboard pages (`kennel_panel_base.html`) | CDN: `<script src="https://cdn.tailwindcss.com">` |

When adding **dashboard** templates: use Tailwind utility classes freely — the CDN build supports all of them without compilation.

When adding **public** templates: ensure `output.css` is regenerated after introducing new utility classes (run `tailwindcss.exe` or the `package.json` build script).

Do not mix loading strategies within a section, and do not write custom `<style>` blocks in individual templates.

## JavaScript

All JavaScript is **vanilla JS** — no frameworks. Scripts are embedded directly in base templates. Never add external JS libraries without discussion.

Scripts embedded in `kennel_panel_base.html`:

| Script | Behavior |
|--------|----------|
| Sidebar toggle | Responsive sidebar open/close on mobile; controlled by `toggleSidebar()` |
| Toast auto-dismiss | Django `messages` rendered as toasts; auto-removed after 5 seconds with fade |
| Lightbox | Fullscreen image viewer; `openLightbox(url)` / `closeLightbox()` / ESC key |
| File upload UI | Custom feedback on `<input type="file">` — shows filename, changes border color |

## Security

| Mechanism | Implementation |
|-----------|---------------|
| CSP | `django-csp` middleware; `CSP_SCRIPT_SRC = ("'self'",)` — no inline scripts in production |
| CAPTCHA | Cloudflare Turnstile on login and register; verified server-side via `accounts/utils.py:verify_turnstile()` |
| Field encryption | `Buyer.id_number` stored encrypted via `django-encrypted-model-fields`; key from `FIELD_ENCRYPTION_KEY` env var |
| CSRF | `{% csrf_token %}` required on every POST form |
| Auth | `@login_required` on all dashboard views; unauthenticated requests redirect to `LOGIN_URL = "login"` |
| Ownership | Every view filters querysets by `breeder=request.user` — users can never access another breeder's data |

## Media Files

`MEDIA_ROOT = BASE_DIR / 'media'`, served at `/media/`. In production, delegate serving to nginx or object storage — Django only serves media in `DEBUG=True` mode.

| Upload path | Model field |
|-------------|-------------|
| `dogs/profiles/` | `Dog.profile_picture` |
| `puppies/profiles/` | `Puppy.profile_picture` |
| `litters/covers/` | `Litter.cover_photo` |
| `measurements/photos/` | `Measurement.photo` |

## Planned but Not Yet Implemented

The following features have placeholder sidebar links or commented-out model fields but no implementation yet:

- Billing views (payment processing, subscription management)
- Medical Records dashboard panel
- Documents dashboard panel
- Document generator
- User profile / settings page
- Cloud file storage for `MedicalRecord.result_file` and `DocumentRecord.document_file` (fields commented out in `kennel/models.py`)