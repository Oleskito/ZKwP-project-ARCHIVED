from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0008_payment_stripe_invoice_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscriptionplan",
            name="tier_weight",
            field=models.PositiveSmallIntegerField(
                default=0,
                verbose_name="Waga planu (ranking: Start=10, Pro=20, VIP=30)",
            ),
        ),
    ]
