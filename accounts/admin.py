from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Breeder


class BreederAdmin(UserAdmin):
    list_display = ("username", "email", "kennel_name", "branch", "is_staff")
    # Dodajemy Twoje nowe pola z models.py do panelu administratora
    fieldsets = UserAdmin.fieldsets + (
        (
            "Dane Hodowli ZKwP",
            {"fields": ("kennel_name", "branch", "membership_number")},
        ),
        (
            "Dane Adresowe",
            {
                "fields": (
                    "address_line_one",
                    "address_line_two",
                    "city",
                    "region",
                    "postal_code",
                    "country",
                )
            },
        ),
        ("Subskrypcja", {"fields": ("subscription_valid_until",)}),
    )


admin.site.register(Breeder, BreederAdmin)
