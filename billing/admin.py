from django.contrib import admin

from .models import Payment, SubscriptionPlan


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "breeder",
        "plan",
        "amount",
        "payment_date",
        "status",
    )
    ordering = ("payment_date", "breeder")
    list_filter = ("breeder", "plan", "status", "payment_date")
    search_fields = ("breeder", "plan", "payment_date")

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["amount", "plan", "breeder", "payment_date"]
        return []


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_days")
