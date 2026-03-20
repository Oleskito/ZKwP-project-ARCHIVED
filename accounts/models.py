from django.contrib.auth.models import AbstractUser
from django.db import models
from django_countries.fields import CountryField


class Breeder(AbstractUser):
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

    # current_plan = models.ForeignKey('billing.SubscriptionPlan', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="aktualna plan subskrybcji")
    def __str__(self):
        if self.kennel_name:
            return f"{self.first_name} {self.last_name} ({self.kennel_name})"
        return self.username
