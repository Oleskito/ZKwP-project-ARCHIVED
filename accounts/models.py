import uuid

import encrypted_model_fields.fields as encrypted_fields
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django_countries.fields import CountryField


class BreederManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Adres email jest wymagany")
        if not password:
            raise ValueError("Hasło jest wymagane")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class Breeder(AbstractUser):
    class ZKwPBranch(models.TextChoices):
        BEDZIN = "Będzin", "Będzin"
        BIALYSTOK = "Białystok", "Białystok"
        BIELSKO_BIALA = "Bielsko-Biała", "Bielsko-Biała"
        BYDGOSZCZ = "Bydgoszcz", "Bydgoszcz"
        BYTOM = "Bytom", "Bytom"
        CHOJNICE = "Chojnice", "Chojnice"
        CHORZOW = "Chorzów", "Chorzów"
        CZESTOCHOWA = "Częstochowa", "Częstochowa"
        GDYNIA = "Gdynia", "Gdynia"
        GNIEZNO = "Gniezno", "Gniezno"
        GORZOW_WIELKOPOLSKI = "Gorzów Wielkopolski", "Gorzów Wielkopolski"
        GRODZISK_MAZOWIECKI = "Grodzisk Mazowiecki", "Grodzisk Mazowiecki"
        GRUDZIADZ = "Grudziądz", "Grudziądz"
        INOWROCLAW = "Inowrocław", "Inowrocław"
        JELENIA_GORA = "Jelenia Góra", "Jelenia Góra"
        KALISZ = "Kalisz", "Kalisz"
        KATOWICE = "Katowice", "Katowice"
        KIELCE = "Kielce", "Kielce"
        KOSZALIN = "Koszalin", "Koszalin"
        KRAKOW = "Kraków", "Kraków"
        KROSNO = "Krosno", "Krosno"
        LEGIONOWO = "Legionowo", "Legionowo"
        LEGNICA = "Legnica", "Legnica"
        LUBLIN = "Lublin", "Lublin"
        LODZ = "Łódź", "Łódź"
        NOWY_SACZ = "Nowy Sącz", "Nowy Sącz"
        NOWY_TARG = "Nowy Targ", "Nowy Targ"
        OLSZTYN = "Olsztyn", "Olsztyn"
        OPOLE = "Opole", "Opole"
        PIASECZNO = "Piaseczno", "Piaseczno"
        PIOTRKOW_TRYBUNALSKI = "Piotrków Trybunalski", "Piotrków Trybunalski"
        PLOCK = "Płock", "Płock"
        POZNAN = "Poznań", "Poznań"
        PRZEMYSL = "Przemyśl", "Przemyśl"
        RACIBORZ = "Racibórz", "Racibórz"
        RADOM = "Radom", "Radom"
        RYBNIK = "Rybnik", "Rybnik"
        RZESZOW = "Rzeszów", "Rzeszów"
        SLUPSK = "Słupsk", "Słupsk"
        SOPOT = "Sopot", "Sopot"
        SZCZECIN = "Szczecin", "Szczecin"
        TORUN = "Toruń", "Toruń"
        WALBRZYCH = "Wałbrzych", "Wałbrzych"
        WARSZAWA = "Warszawa", "Warszawa"
        WIELICZKA = "Wieliczka", "Wieliczka"
        WLOCLAWEK = "Włocławek", "Włocławek"
        WROCLAW = "Wrocław", "Wrocław"
        ZABRZE = "Zabrze", "Zabrze"
        ZAKOPANE = "Zakopane", "Zakopane"
        ZGIERZ = "Zgierz", "Zgierz"
        ZIELONA_GORA = "Zielona Góra", "Zielona Góra"

    class AccountStatus(models.TextChoices):
        ACTIVE = "active", "Aktywny"
        GRACE_PERIOD = "grace_period", "Okres karencji"
        READ_ONLY = "read_only", "Tylko odczyt"
        FROZEN = "frozen", "Zamrożony"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Data rejestracji"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")

    username = None
    email = models.EmailField(unique=True, verbose_name="Adres email")
    mfa_verification = models.BooleanField(
        default=False, verbose_name="Dwuetapowa weryfikacja"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = BreederManager()

    # adres:
    address_line_one = models.CharField(
        max_length=80, blank=True, verbose_name="Ulica i nr domu"
    )
    address_line_two = models.CharField(
        max_length=30, blank=True, verbose_name="Nr mieszkania"
    )
    city = models.CharField(max_length=50, blank=True, verbose_name="Miasto")
    region = models.CharField(max_length=50, blank=True, verbose_name="Województwo")
    postal_code = models.CharField(
        max_length=15, blank=True, verbose_name="Kod pocztowy"
    )
    country = CountryField(default="PL", verbose_name="Kraj")

    # hodowla:
    kennel_name = models.CharField(
        max_length=80, blank=True, verbose_name="Przydomek hodowlany"
    )

    branch = models.CharField(
        max_length=50, choices=ZKwPBranch.choices, blank=True, null=True
    )  # type:ignore
    membership_number = models.CharField(
        max_length=30, blank=True, verbose_name="Numer legitymacji ZKwP"
    )
    kennel_registration_number = models.CharField(
        max_length=50, blank=True, verbose_name="Numer rejestracji przydomka (np. FCI)"
    )

    # płatności:
    subscription_valid_until = models.DateTimeField(
        blank=True, null=True, verbose_name="Subskrypcja aktywna do..."
    )
    subscription_activated_at = models.DateTimeField(
        blank=True, null=True, verbose_name="Data aktywacji subskrypcji"
    )

    current_plan = models.ForeignKey(
        "billing.SubscriptionPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="aktualny plan subskrypcji",
    )
    wants_email_notifications = models.BooleanField(
        default=True, verbose_name="Otrzymuj przypomnienia e-mail"
    )

    phone_number = models.CharField(
        max_length=20, blank=True, verbose_name="Nr telefonu"
    )
    is_verified = models.BooleanField(default=False, verbose_name="Zweryfikowany")
    tos_accepted_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Data akceptacji regulaminu"
    )
    kennel_logo = models.ImageField(
        upload_to="kennel_logos/", null=True, blank=True, verbose_name="Logo hodowli"
    )
    company_name = models.CharField(
        max_length=150, blank=True, verbose_name="Nazwa firmy"
    )
    nip = encrypted_fields.EncryptedCharField(
        max_length=15, blank=True, verbose_name="NIP"
    )
    pesel = encrypted_fields.EncryptedCharField(
        max_length=11,
        blank=True,
        null=True,
        verbose_name="PESEL",
        validators=[
            RegexValidator(r"^\d{11}$", "PESEL musi składać się z dokładnie 11 cyfr.")
        ],
    )
    tax_office = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Urząd skarbowy"
    )
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data urodzenia")
    notes = models.CharField(
        max_length=500, blank=True, verbose_name="Notatki np. strona internetowa"
    )

    stripe_customer_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="ID klienta Stripe",
    )
    stripe_subscription_id = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="ID subskrypcji Stripe",
    )

    @property
    def account_status(self) -> str:
        if not self.subscription_valid_until:
            return self.AccountStatus.FROZEN
        now = timezone.now()
        delta = now - self.subscription_valid_until
        days = delta.total_seconds() / 86400
        if days <= 0:
            return self.AccountStatus.ACTIVE
        elif days <= 3:
            return self.AccountStatus.GRACE_PERIOD
        elif days <= 180:
            return self.AccountStatus.READ_ONLY
        return self.AccountStatus.FROZEN

    @property
    def is_continuity_broken(self) -> bool:
        if not self.subscription_valid_until:
            return True
        return (
            timezone.now() - self.subscription_valid_until
        ).total_seconds() > 7 * 86400

    @property
    def days_remaining(self) -> int:
        if not self.subscription_valid_until:
            return 0
        delta = self.subscription_valid_until - timezone.now()
        return max(0, int(delta.total_seconds() / 86400))

    @property
    def pit_required_months(self) -> int:
        if not self.current_plan:
            return 10
        name = self.current_plan.name.lower()
        if "vip" in name:
            return 3
        if "pro" in name:
            return 7
        return 10

    @property
    def paid_months_last_15(self) -> int:
        from billing.models import Payment

        cutoff = timezone.now() - relativedelta(months=15)
        payments = self.payments.filter(
            status=Payment.Status.COMPLETED, payment_date__gte=cutoff
        ).select_related("plan")
        total = 0
        for p in payments:
            total += 12 if getattr(p.plan, "interval", "") == "yearly" else 1
        return total

    @property
    def has_pit_access(self) -> bool:
        if not self.current_plan or self.is_continuity_broken:
            return False
        return self.paid_months_last_15 >= self.pit_required_months

    @property
    def pit_access_months_remaining(self) -> int | None:
        if not self.current_plan:
            return None
        return max(0, self.pit_required_months - self.paid_months_last_15)

    def extend_subscription(self, months: int = 1) -> None:
        now = timezone.now()
        if self.subscription_valid_until and not self.is_continuity_broken:
            self.subscription_valid_until += relativedelta(months=months)
        else:
            self.subscription_activated_at = now
            self.subscription_valid_until = now + relativedelta(months=months)
        self.save(
            update_fields=["subscription_valid_until", "subscription_activated_at"]
        )

    def __str__(self):
        if self.kennel_name:
            return (
                f"{self.email} {self.first_name} {self.last_name} ({self.kennel_name})"
            )
        return f"{self.email} {self.first_name} {self.last_name}"
