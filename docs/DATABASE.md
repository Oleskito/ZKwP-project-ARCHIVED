# Database

## Rules

1. **PostgreSQL only.** Never use SQLite or any other database engine, including in tests.
2. **Credentials from environment variables only.** Never hardcode database credentials. All six DB settings come from `.env`: `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.
3. **UUID primary keys on every model.** Always add `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)` as the first field.
4. **Timestamps on every model.** Always add `created_at = models.DateTimeField(auto_now_add=True)` and `updated_at = models.DateTimeField(auto_now=True)` after `id`.
5. **Never skip migrations.** All schema changes go through `makemigrations` + `migrate`. Never edit the database schema directly via SQL or admin tools.
6. **`on_delete` must always be explicit.** Use `PROTECT` for reference/lookup data (Breed, SubscriptionPlan, TreatmentType). Use `SET_NULL` for optional parent relationships where the child record still makes sense without the parent. Use `CASCADE` only when child records are meaningless without the parent (e.g., Dog → Breeder).
7. **No raw SQL.** Use the Django ORM exclusively. `Manager.raw()` and `connection.cursor()` are forbidden unless documented with a clear reason.

## Required Environment Variables

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=<database name>
DB_USER=<username>
DB_PASSWORD=<password>
DB_HOST=<host>
DB_PORT=5432
SECRET_KEY=<django secret key>
FIELD_ENCRYPTION_KEY=<fernet key for Buyer.id_number>
TURNSTILE_SECRET_KEY=<cloudflare turnstile secret>
```

## Models Reference

### `accounts` app

#### `Breeder` (extends `AbstractUser`)

The sole user model (`AUTH_USER_MODEL = "accounts.Breeder"`). The `username` field is removed; `email` is the login identifier.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `email` | `EmailField(unique=True)` | `USERNAME_FIELD` |
| `first_name` | `CharField(150)` | From `AbstractUser` |
| `last_name` | `CharField(150)` | From `AbstractUser` |
| `address_line_one` | `CharField(80)` | |
| `address_line_two` | `CharField(30)` | |
| `city` | `CharField(50)` | |
| `region` | `CharField(50)` | |
| `postal_code` | `CharField(15)` | |
| `country` | `CountryField` | Default `"PL"` |
| `kennel_name` | `CharField(80)` | Breeding kennel name ("przydomek") |
| `branch` | `CharField(80)` | ZKwP branch name |
| `membership_number` | `CharField(30)` | ZKwP membership card number |
| `subscription_valid_until` | `DateField` | null/blank |
| `current_plan` | `ForeignKey(SubscriptionPlan, SET_NULL)` | null/blank |
| `phone_number` | `CharField(20)` | |
| `is_verified` | `BooleanField` | Default `False` |
| `tos_accepted_at` | `DateTimeField` | null/blank |
| `created_at` | `DateTimeField(auto_now_add)` | |
| `updated_at` | `DateTimeField(auto_now)` | |

---

### `kennel` app

#### `Breed`

Reference data for dog breeds. Managed exclusively via the admin panel — no user-facing forms.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `name` | `CharField(80)` | |
| `is_small_breed` | `BooleanField` | Default `False` |
| `required_tests` | `JSONField` | Default `{}` — stores required health test names |
| `country_of_origin` | `CharField(30)` | |
| `created_at` / `updated_at` | `DateTimeField` | |

#### `Dog`

Registered adult dogs belonging to a breeder.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `breeder` | `ForeignKey(Breeder, CASCADE)` | Owner |
| `breed` | `ForeignKey(Breed, PROTECT)` | null/blank |
| `father` | `ForeignKey("self", SET_NULL)` | null/blank; `related_name="father_of"` |
| `mother` | `ForeignKey("self", SET_NULL)` | null/blank; `related_name="mother_of"` |
| `name` | `CharField(100)` | |
| `origin_kennel` | `CharField(100)` | Kennel of origin ("przydomek") |
| `gender` | `CharField` | Choices: `male` / `female` |
| `breeding_status` | `CharField` | Choices: `in_preparation`, `active`, `inactive`, `sold`, `deceased` |
| `birth_date` | `DateField` | null/blank |
| `pkr_number` | `CharField(40)` | |
| `branch_registration_number` | `CharField(20)` | |
| `country_of_registration` | `CountryField` | Default `"PL"` |
| `chip_number` | `CharField(20)` | null/blank; unique per breeder |
| `tattoo_number` | `CharField(20)` | null/blank; unique per breeder |
| `color` | `CharField(45)` | |
| `is_archived` | `BooleanField` | Default `False`; **auto-set by `save()`** |
| `co_owner_first_name` / `co_owner_last_name` | `CharField(30)` | |
| `co_owner_address_line_one` | `CharField(80)` | |
| `co_owner_address_line_two` | `CharField(30)` | |
| `co_owner_city` | `CharField(50)` | |
| `co_owner_region` | `CharField(50)` | |
| `co_owner_postal_code` | `CharField(15)` | |
| `co_owner_country` | `CountryField` | Default `"PL"` |
| `profile_picture` | `ImageField` | Upload to `dogs/profiles/`; null/blank |
| `created_at` / `updated_at` | `DateTimeField` | |

**DB constraints:**
- `unique_chip_per_breeder`: unique `(breeder, chip_number)`
- `unique_tattoo_per_breeder`: unique `(breeder, tattoo_number)`

**`save()` side effect:** Automatically sets `is_archived = True` when `breeding_status` is `inactive`, `sold`, or `deceased`. Sets it to `False` otherwise. Never set `is_archived` manually.

**`clean()` validation:** Father must have `gender="male"`; mother must have `gender="female"`.

**Properties:**
- `current_weight` → most recent `Measurement.weight` for this dog (or `None`)
- `current_height` → most recent `Measurement.height` for this dog (or `None`)

#### `Litter`

A breeding event, optionally linking internal dogs as parents or storing external parent data as JSON.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `breeder` | `ForeignKey(Breeder, CASCADE)` | |
| `mother` | `ForeignKey(Dog, SET_NULL)` | null/blank; `related_name="litters_as_mother"` |
| `father` | `ForeignKey(Dog, SET_NULL)` | null/blank; `related_name="litters_as_father"` |
| `breed` | `ForeignKey(Breed, PROTECT)` | null/blank |
| `mating_place` | `CharField(200)` | |
| `mating_date_start` / `mating_date_end` | `DateField` | null/blank |
| `birth_date` | `DateField` | null/blank |
| `males_count` / `females_count` / `deceased_count` | `IntegerField` | null/blank |
| `litter_letter` | `CharField(10)` | |
| `status` | `CharField` | Choices: `planned`, `mated`, `empty`, `born`, `reported`, `inspected`, `archived` |
| `father_data_snapshot` | `JSONField` | External father data; default `{}`; **mutually exclusive with `father` FK** |
| `mother_data_snapshot` | `JSONField` | External mother data; default `{}`; **mutually exclusive with `mother` FK** |
| `cover_photo` | `ImageField` | Upload to `litters/covers/`; null/blank |
| `created_at` / `updated_at` | `DateTimeField` | |

**Invariant (enforced by `clean()` called from `save()`):** A litter cannot simultaneously have both `father` (internal FK) and a non-empty `father_data_snapshot`. Same rule applies to mother. Violating this raises `ValidationError`.

#### `Puppy`

A puppy within a litter. Can be promoted to a full `Dog` record.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `breeder` | `ForeignKey(Breeder, CASCADE)` | |
| `litter` | `ForeignKey(Litter, CASCADE)` | |
| `adult_dog_profile` | `OneToOneField(Dog, SET_NULL)` | null/blank; `related_name="original_puppy"`; set when puppy is promoted |
| `name` | `CharField(100)` | |
| `color` | `CharField(45)` | |
| `gender` | `CharField` | Choices: `male` / `female` |
| `chip_number` | `CharField(20)` | null/blank; unique per breeder |
| `tattoo_number` | `CharField(20)` | null/blank; unique per breeder |
| `internal_id` | `CharField(100)` | E.g., collar color for identification before chipping |
| `status` | `CharField` | Choices: `available`, `reserved`, `booked`, `staying`, `sold`, `deceased` |
| `profile_picture` | `ImageField` | Upload to `puppies/profiles/`; null/blank |
| `created_at` / `updated_at` | `DateTimeField` | |

**DB constraints:**
- `puppy_unique_chip_per_breeder`: unique `(breeder, chip_number)`
- `puppy_unique_tattoo_per_breeder`: unique `(breeder, tattoo_number)`

**Properties:** `current_weight`, `current_height` — same pattern as `Dog`.

#### `Buyer`

Buyer contact data attached to a breeder's account. Contains sensitive PII.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `breeder` | `ForeignKey(Breeder, CASCADE)` | |
| `first_name` / `last_name` | `CharField(30)` | |
| `phone_number` | `CharField(18)` | |
| `email` | `EmailField(50)` | |
| `id_number` | `EncryptedCharField(25)` | PESEL / document number — **stored encrypted at the DB level** |
| `address_line_one` | `CharField(80)` | |
| `address_line_two` | `CharField(80)` | |
| `city` | `CharField(50)` | |
| `region` | `CharField(50)` | |
| `postal_code` | `CharField(15)` | |
| `country` | `CountryField` | Default `"PL"` |
| `created_at` / `updated_at` | `DateTimeField` | |

#### `TreatmentType`

Lookup table for types of medical procedures or health tests.

| Field | Type |
|-------|------|
| `id` | `UUIDField` PK |
| `name` | `CharField(100)` |
| `created_at` / `updated_at` | `DateTimeField` |

#### `TreatmentResult`

Lookup table for possible results of a `TreatmentType`. Chained to `TreatmentType` via `django-smart-selects`.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `treatment_type` | `ForeignKey(TreatmentType, PROTECT)` | Results are scoped to a type |
| `name` | `CharField(100)` | |
| `created_at` / `updated_at` | `DateTimeField` | |

#### `MedicalRecord`

A medical event linked to exactly one of: a dog, a puppy, or a litter.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `dog` | `ForeignKey(Dog, CASCADE)` | null/blank |
| `puppy` | `ForeignKey(Puppy, CASCADE)` | null/blank |
| `litter` | `ForeignKey(Litter, CASCADE)` | null/blank |
| `date` | `DateField` | null/blank |
| `treatment_type` | `ForeignKey(TreatmentType, PROTECT)` | |
| `result` | `ChainedForeignKey(TreatmentResult)` | Filtered by `treatment_type`; auto-chosen if only one result exists |
| `created_at` / `updated_at` | `DateTimeField` | |

**DB constraint:** `medical_record_one_animal_source` — exactly one of `dog`, `puppy`, `litter` must be non-null.

#### `DocumentRecord`

A document record linked to exactly one of: a dog, a puppy, or a litter.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `dog` / `puppy` / `litter` | FK (CASCADE) | null/blank — exactly one must be set |
| `date` | `DateField` | null/blank |
| `category` | `CharField` | Choices: `pedigree`, `contract`, `certificate`, `other`; default `other` |
| `document_name` | `CharField(50)` | null/blank |
| `created_at` / `updated_at` | `DateTimeField` | |

**DB constraint:** `document_record_one_animal_source` — same pattern as `MedicalRecord`.

#### `Measurement`

A physical measurement entry linked to exactly one dog or puppy. All measurement parameters are optional — a record can capture just weight, or any combination of fields.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `dog` | `ForeignKey(Dog, CASCADE)` | null/blank — exactly one of dog/puppy must be set |
| `puppy` | `ForeignKey(Puppy, CASCADE)` | null/blank |
| `date` | `DateField` | Required |
| `weight` | `FloatField` | null/blank; kg |
| `height` | `FloatField` | null/blank; cm (withers height) |
| `chest_girth` | `FloatField` | null/blank; cm |
| `head_girth` | `FloatField` | null/blank; cm |
| `body_length` | `FloatField` | null/blank; cm |
| `temperature` | `FloatField` | null/blank; °C |
| `bcs` | `PositiveSmallIntegerField` | null/blank; Body Condition Score 1–9 |
| `photo` | `ImageField` | Upload to `measurements/photos/`; null/blank |
| `notes` | `TextField` | null/blank |
| `created_at` | `DateTimeField(auto_now_add)` | Note: no `updated_at` on this model |

**Default ordering:** `['-date', '-created_at']`

**DB constraint:** `measurement_one_animal_source` — exactly one of `dog` / `puppy` is non-null.

---

### `billing` app

#### `SubscriptionPlan`

Defines available subscription tiers. Managed via admin only.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `name` | `CharField(60)` | |
| `price` | `DecimalField(10, 2)` | |
| `duration_days` | `PositiveBigIntegerField` | |
| `created_at` / `updated_at` | `DateTimeField` | |

#### `Payment`

A payment record. Both `breeder` and `plan` use `PROTECT` to prevent data loss — a plan or user cannot be deleted while payments exist.

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUIDField` | PK |
| `breeder` | `ForeignKey(Breeder, PROTECT)` | `related_name="payments"` |
| `plan` | `ForeignKey(SubscriptionPlan, PROTECT)` | `related_name="payments"` |
| `amount` | `DecimalField(10, 2)` | Auto-filled from `plan.price` if not provided on creation |
| `payment_date` | `DateTimeField` | null/blank |
| `status` | `CharField` | Choices: `pending`, `completed`, `failed`, `cancelled`, `refunded`; default `"pending"` |
| `created_at` / `updated_at` | `DateTimeField` | |

**`save()` side effect:** If `pk` is None (new record) and `amount` is not set, `amount` is auto-filled from `self.plan.price`.

## Migration State

| App | Latest migration |
|-----|-----------------|
| `accounts` | `0002_breeder_current_plan` |
| `kennel` | `0011_dog_adult_dog_profile` |
| `billing` | `0002_subscriptionplan_updated_at` |

Always run `python manage.py showmigrations` to verify current state before creating new migrations.