from django.contrib import admin

from .models import (
    Breed,
    Buyer,
    Dog,
    Litter,
    MedicalRecord,
    Puppy,
    TreatmentResult,
    TreatmentType,
    DocumentRecord,
    Measurement,
)


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "breeder",
        "origin_kennel",
        "gender",
        "breeding_status",
        "chip_number",
        "is_archived",
    )
    list_filter = ("breeding_status", "gender", "is_archived", "breeder")
    search_fields = ("name", "chip_number", "tattoo_number", "pkr_number")
    ordering = ("breeding_status", "name")


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    list_display = ("name", "is_small_breed", "required_tests")
    list_filter = ("is_small_breed", "required_tests")
    search_fields = ("name", "required_tests")
    ordering = ["name"]


@admin.register(Litter)
class LitterAdmin(admin.ModelAdmin):
    list_display = ("litter_letter", "birth_date", "breed", "status")
    list_filter = ("litter_letter", "birth_date", "status")
    ordering = ("birth_date", "status")


@admin.register(Puppy)
class PuppyAdmin(admin.ModelAdmin):
    list_display = ("name", "chip_number", "get_birth_date", "status")
    list_filter = ("gender", "status")
    search_fields = ("name", "chip_number", "tattoo_number", "pkr_number")
    ordering = ["name"]

    def get_birth_date(self, obj):
        if obj.litter:
            return obj.litter.birth_date
        return "-"


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "updated_at")
    list_filter = ["updated_at"]
    ordering = ("first_name", "last_name")


@admin.register(TreatmentType)
class TreatmentTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(TreatmentResult)
class TreatmentResultAdmin(admin.ModelAdmin):
    list_display = ("name", "treatment_type")
    list_filter = ["treatment_type"]


@admin.register(MedicalRecord)
class MedicalResultAdmin(admin.ModelAdmin):
    list_display = ("date", "get_animal", "treatment_type", "result")

    def get_animal(self, obj):
        return obj.dog if obj.dog else obj.puppy

    get_animal.short_description = "Zwierzę"


@admin.register(DocumentRecord)
class DocumentRecordAdmin(admin.ModelAdmin):
    list_display = ("date", "get_animal", "category", "document_name")

    def get_animal(self, obj):
        if obj.dog:
            return obj.dog
        elif obj.puppy:
            return obj.puppy
        return obj.litter

    get_animal.short_description = "Zwierzę"


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    # Co widać na głównej liście pomiarów
    list_display = (
        "get_animal",
        "date",
        "weight",
        "height",
        "temperature",
        "created_at",
    )

    # Filtrowanie po prawej stronie
    list_filter = ("date", "created_at")

    # Wyszukiwarka (po imieniu psa lub szczeniaka)
    search_fields = ("dog__name", "puppy__name")

    # Podział formularza na sekcje!
    fieldsets = (
        ("Powiązanie i Data", {"fields": ("date", "dog", "puppy")}),
        ("Pomiary podstawowe", {"fields": ("weight", "height", "temperature")}),
        (
            "Pomiary zaawansowane (Opcjonalne)",
            {
                "classes": (
                    "collapse",
                ),  # Ta klasa sprawia, że sekcja jest domyślnie zwinięta!
                "fields": ("chest_girth", "head_girth", "body_length", "bcs"),
            },
        ),
        ("Dziennik", {"fields": ("notes",)}),
    )

    # Funkcja pomocnicza do list_display, żeby ładnie wyświetlać kto był mierzony
    def get_animal(self, obj):
        if obj.dog:
            return f"Pies: {obj.dog.name}"
        if obj.puppy:
            return f"Szczeniak: {obj.puppy.name}"
        return "Brak powiązania"

    get_animal.short_description = "Zwierzę"

    get_animal.short_description = "Zwierzę"
