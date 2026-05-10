from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("billing", "0007_subscriptionplan_pit_access_monthly_threshold"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="stripe_checkout_session_id",
            field=models.CharField(
                blank=True,
                default="",
                max_length=200,
                verbose_name="ID sesji Stripe",
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="invoice_url",
            field=models.URLField(
                blank=True,
                default="",
                max_length=500,
                verbose_name="Link do faktury",
            ),
        ),
    ]