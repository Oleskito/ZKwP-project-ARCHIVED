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
)


@admin.register(Dog)
class DogAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "breeder",
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
