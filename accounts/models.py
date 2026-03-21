from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
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

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class Breeder(AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name="Adres email")

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
    branch = models.CharField(max_length=80, blank=True, verbose_name="Oddział ZKwP")
    membership_number = models.CharField(
        max_length=30, blank=True, verbose_name="Numer legitymacji ZKwP"
    )

    # płatności:
    subscription_valid_until = models.DateField(
        blank=True, null=True, verbose_name="Subskrybcja aktywna do..."
    )

    current_plan = models.ForeignKey(
        "billing.SubscriptionPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="aktualny plan subskrybcji",
    )

    def __str__(self):
        if self.kennel_name:
            return (
                f"{self.email} {self.first_name} {self.last_name} ({self.kennel_name})"
            )
        return f"{self.email} {self.first_name} {self.last_name}"
