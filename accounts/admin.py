from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import BreederCreationForm, BreederChangeForm
from .models import Breeder


class BreederAdmin(UserAdmin):
    add_form = BreederCreationForm
    form = BreederChangeForm  # Dodajemy też formularz dla edycji

    list_display = ("email", "first_name", "last_name", "kennel_name", "branch")
    ordering = ("email", "first_name", "last_name")
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informacje osobiste", {"fields": ("first_name", "last_name")}),
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

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password", "first_name", "last_name"),
        }),
    )

    # ZMIANA: Usunąłem save_model! Nie jest już potrzebne i nie zepsuje hasła.


admin.site.register(Breeder, BreederAdmin)