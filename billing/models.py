from django.conf import settings
from django.db import models
import uuid


class SubscriptionPlan(models.Model):
    class Interval(models.TextChoices):
        MONTHLY = 'monthly', 'Miesięczny'
        YEARLY = 'yearly', 'Roczny'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania pakietu")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")

    name = models.CharField(max_length=60, verbose_name="Nazwa planu")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena")
    interval = models.CharField(
        max_length=20,
        choices=Interval.choices,
        default=Interval.MONTHLY,
        verbose_name="Okres rozliczeniowy"
    )
    max_litters_per_year = models.PositiveBigIntegerField(blank=True, null=True, verbose_name="Maksymalna liczba miotów rocznie")
    max_breeding_dogs = models.PositiveBigIntegerField(blank=True, null=True, verbose_name="Maksymalna liczba aktywnych psów")
    storage_gb = models.PositiveIntegerField(verbose_name="Pojemność dysku (GB)", blank=True, null=True)
    pit_access_monthly_threshold = models.PositiveSmallIntegerField(
        blank=True, null=True,
        verbose_name="Próg miesięcy dla dostępu do PiT (miesięczny)"
    )
    tier_weight = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Waga planu (ranking: Start=10, Pro=20, VIP=30)",
    )

    def __str__(self):
        return f"{self.name}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Oczekująca"
        COMPLETED = "completed", "Opłacona"
        FAILED = "failed", "Nieudana"
        CANCELLED = "cancelled", "Anulowana"
        REFUNDED = "refunded", "Zwrócona"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia rekordu")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji rekordu")

    breeder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Hodowca",
        related_name="payments",
    )
    plan = models.ForeignKey(
        "billing.SubscriptionPlan",
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name="Plan subskrybcji",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kwota")
    payment_date = models.DateTimeField(
        blank=True, null=True, verbose_name="Data płatności"
    )
    # zakładając że data płatnosci to moment stworzenia rekordu można zmienić na auto_now_add = True

    status = models.CharField(
        max_length=20,
        default="pending",
        choices=Status.choices, #type: ignore
        verbose_name="Status płatności",
    )

    stripe_checkout_session_id = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="ID sesji Stripe",
    )
    invoice_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Link do faktury",
    )

    def save(self, *args, **kwargs):
        # Jeśli to nowa płatność i nie podaliśmy kwoty ręcznie
        if not self.pk and not self.amount:
            self.amount = self.plan.price
        super().save(*args, **kwargs)
