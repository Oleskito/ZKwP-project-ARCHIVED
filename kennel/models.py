import encrypted_model_fields.fields as encrypted_fields
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django_countries.fields import CountryField
from smart_selects.db_fields import ChainedForeignKey
import uuid


class Dog(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Samiec"
        FEMALE = "female", "Samica"

    class BreedingStatus(models.TextChoices):
        IN_PREPARATION = "in_preparation", "W przygotowaniu (młodzież)"
        ACTIVE = "active", "Aktywny hodowlanie"
        INACTIVE = "inactive", "Nieaktywny hodowlanie"
        SOLD = "sold", "Sprzedany"
        DECEASED = "deceased", "Zmarły"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")

    # Klucze obce:
    father = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Ojciec",
        related_name="father_of",
    )
    mother = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Matka",
        related_name="mother_of",
    )
    breed = models.ForeignKey(
        "kennel.Breed",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Rasa psa",
    )
    breeder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Hodowca"
    )

    name = models.CharField(
        max_length=100,
        verbose_name="Imię psa",
    )
    origin_kennel = models.CharField(max_length=100, blank=True, verbose_name="Przydomek psa")
    gender = models.CharField(
        max_length=10,
        blank=True,
        choices=Gender.choices, #type:ignore
        verbose_name="Płeć psa",
    )
    breeding_status = models.CharField(
        max_length=30,
        blank=True,
        choices=BreedingStatus.choices, #type:ignore
        verbose_name="Status hodowlany",
    )
    birth_date = models.DateField(
        blank=True, null=True, verbose_name="Data urodzenia psa"
    )
    pkr_number = models.CharField(max_length=40, blank=True, verbose_name="Numer PKR")
    branch_registration_number = models.CharField(
        max_length=20, blank=True, verbose_name="Numer rejestracyjny oddziału"
    )
    country_of_registration = CountryField(default="PL", verbose_name="Kraj")
    chip_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Numer chipa"
    )
    tattoo_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Numer tatuażu"
    )
    color = models.CharField(max_length=45, blank=True, verbose_name="Umaszczenie")
    is_archived = models.BooleanField(
        default=False, verbose_name="Czy pies jest zarchiwizowany"
    )

    # DANE O WSPÓŁWŁAŚCICIELU
    co_owner_first_name = models.CharField(
        max_length=30, blank=True, verbose_name="Imię współwłaściciela"
    )
    co_owner_last_name = models.CharField(
        max_length=30, blank=True, verbose_name="Nazwisko współwłaściciela"
    )
    co_owner_address_line_one = models.CharField(
        max_length=80, blank=True, verbose_name="Ulica i nr domu współwłaściciela"
    )
    co_owner_address_line_two = models.CharField(
        max_length=30, blank=True, verbose_name="Nr mieszkania"
    )
    co_owner_city = models.CharField(max_length=50, blank=True, verbose_name="Miasto")
    co_owner_region = models.CharField(
        max_length=50, blank=True, verbose_name="Województwo"
    )
    co_owner_postal_code = models.CharField(
        max_length=15, blank=True, verbose_name="Kod pocztowy"
    )
    co_owner_country = CountryField(default="PL", verbose_name="Kraj")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["breeder", "chip_number"], name="unique_chip_per_breeder"
            ),
            models.UniqueConstraint(
                fields=["breeder", "tattoo_number"], name="unique_tattoo_per_breeder"
            ),
        ]

    def __str__(self):
        if self.birth_date:
            return f"{self.name} ({self.birth_date})"
        elif  self.chip_number:
            return f"{self.name} Chip: {self.chip_number}"
        elif  self.tattoo_number:
            return f"{self.name} Tatuaż: {self.tattoo_number}"
        return self.name

    def clean(self):
        super().clean()
        if self.father and self.father.gender != 'male':
            raise ValidationError({'father': "Ojcem musi być samiec."})
        if self.mother and self.mother.gender != 'female':
            raise ValidationError({'mother': "Matką musi być samica."})

    def save(self, *args, **kwargs):
        archival_statuses = [
            self.BreedingStatus.INACTIVE,
            self.BreedingStatus.SOLD,
            self.BreedingStatus.DECEASED
        ]

        if self.breeding_status in archival_statuses:
            self.is_archived = True
        else:
            self.is_archived = False

        super().save(*args, **kwargs)


class Breed(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")

    name = models.CharField(max_length=80, verbose_name="Nazwa razy")
    is_small_breed = models.BooleanField(default=False, verbose_name="Mała rasa")
    required_tests = models.JSONField(
        default=dict, blank=True, verbose_name="Wymagane testy"
    )
    country_of_origin = models.CharField(
        max_length=30, blank=True, verbose_name="Kraj pochodzenia"
    )

    def __str__(self):
        return self.name


class Litter(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planowany"
        MATED = "mated", "Krycie wykonane"
        EMPTY = "empty", "Brak ciąży"
        BORN = "born", "Urodzony"
        REPORTED = "reported", "Zgłoszony"
        INSPECTED = "inspected", "Po przeglądzie"
        ARCHIVED = "archived", "Zarchiwizowany"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")

    # Foreign Keys:
    breeder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Hodowca"
    )
    mother = models.ForeignKey(
        "kennel.Dog",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Matka",
        related_name="litters_as_mother",
    )
    father = models.ForeignKey(
        "kennel.Dog",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Ojciec",
        related_name="litters_as_father",
    )
    breed = models.ForeignKey(
        "kennel.Breed",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Rasa psa",
    )

    mating_place = models.CharField(
        max_length=100, blank=True, verbose_name="Miejsce krycia"
    )
    mating_date_start = models.DateField(
        blank=True, null=True, verbose_name="Data początku krycia"
    )
    mating_date_end = models.DateField(
        blank=True, null=True, verbose_name="Data końca krycia"
    )
    birth_date = models.DateField(
        blank=True, null=True, verbose_name="Data narodzin szczeniąt"
    )
    males_count = models.IntegerField(
        blank=True, null=True, verbose_name="Liczba samców"
    )
    females_count = models.IntegerField(
        blank=True, null=True, verbose_name="Liczba samic"
    )
    deceased_count = models.IntegerField(
        blank=True, null=True, verbose_name="Liczba zmarłych szczeniąt"
    )
    litter_letter = models.CharField(
        max_length=10, blank=True, verbose_name="Litera miotu"
    )
    status = models.CharField(
        max_length=20, blank=True, choices=Status.choices, verbose_name="Status miotu" #type:ignore
    )
    # wybierane opcjonalnie jeśli ojciec lub matka jest z innej hodowli:
    father_data_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dane o samcu i właścicielu spoza hodowli",
    )
    mother_data_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dane o samicy i właścicielu spoza hodowli",
    )


class Puppy(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Samiec"
        FEMALE = "female", "Samica"

    class Status(models.TextChoices):
        AVAILABLE = "available", "dostępny"
        RESERVED = "reserved", "zarezerwowany"
        BOOKED = "booked", "Opłacony"
        STAYING = "staying", "Zostaje w hodowli"
        SOLD = "sold", "Wyjechał do nowego domu"
        DECEASED = "deceased", "Zmarły"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")

    # Foreign Keys:
    breeder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Hodowca"
    )
    litter = models.ForeignKey(
        "kennel.Litter", on_delete=models.CASCADE, verbose_name="Miot szczeniaka"
    )

    name = models.CharField(max_length=100, verbose_name="Imię i przydomek szczeniaka")
    color = models.CharField(max_length=45, blank=True, verbose_name="Umaszczenie")
    gender = models.CharField(
        max_length=10, choices=Gender.choices, verbose_name="Płeć" #type:ignore
    )
    chip_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Numer chipa"
    )
    tattoo_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Numer tatuażu"
    )
    internal_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Identyfikator wewnętrzny np. kolor obroży",
    )
    status = models.CharField(
        max_length=50,
        choices=Status.choices, #type:ignore
        blank=True,
        verbose_name="Status szczeniaka",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["breeder", "chip_number"], name="puppy_unique_chip_per_breeder"
            ),
            models.UniqueConstraint(
                fields=["breeder", "tattoo_number"],
                name="puppy_unique_tattoo_per_breeder",
            ),
        ]

    def __str__(self):
        if self.chip_number:
            return f"{self.name} [{self.chip_number}]"
        return self.name


class Buyer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")
    # Foreign keys:
    breeder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Hodowca"
    )
    first_name = models.CharField(max_length=30, verbose_name="Imię kupującego")
    last_name = models.CharField(max_length=30, verbose_name="Nazwisko kupującego")
    phone_number = models.CharField(
        max_length=18, blank=True, verbose_name="Numer telefonu kupującego"
    )
    email = models.EmailField(
        max_length=50, blank=True, verbose_name="Adres email kupującego"
    )
    id_number = encrypted_fields.EncryptedCharField(
        max_length=25,
        blank=True,
        null=True,
        verbose_name="Numer PESEL / dokumentu tożsamości kupującego",
    )
    address_line_one = models.CharField(
        max_length=80, blank=True, verbose_name="Ulica i numer domu"
    )
    address_line_two = models.CharField(
        max_length=80, blank=True, verbose_name="Nr mieszkania"
    )
    city = models.CharField(max_length=50, blank=True, verbose_name="Miasto")
    region = models.CharField(max_length=50, blank=True, verbose_name="Województwo")
    postal_code = models.CharField(
        max_length=15, blank=True, verbose_name="Kod pocztowy"
    )
    country = CountryField(default="PL", verbose_name="Kraj")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class TreatmentType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Typ zabiegu / badania")
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")

    class Meta:
        verbose_name = "Rodzaj zabiegu"
        verbose_name_plural = "Rodzaje zabiegów"

    def __str__(self):
        return self.name


class TreatmentResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")
    treatment_type = models.ForeignKey("kennel.TreatmentType", on_delete=models.PROTECT)
    name = models.CharField(max_length=100, verbose_name="Wynik zabiegu / badania")

    class Meta:
        verbose_name = "Wynik zabiegu / badania"
        verbose_name_plural = "Wyniki zabiegów / badań"

    def __str__(self):
        return f"{self.treatment_type.name}: {self.name}"


class MedicalRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")
    dog = models.ForeignKey(
        "kennel.Dog",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="Pies z naszych psów",
    )
    puppy = models.ForeignKey(
        "kennel.Puppy",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="Szczenię",
    )
    litter = models.ForeignKey(
        'kennel.Litter',
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Miot",
    )
    date = models.DateField(blank=True, null=True, verbose_name="Data badania")

    treatment_type = models.ForeignKey("kennel.TreatmentType", on_delete=models.PROTECT)

    result = ChainedForeignKey(
        "kennel.TreatmentResult",
        chained_field="treatment_type",
        chained_model_field="treatment_type",
        show_all=False,
        auto_choose=True,
        sort=True,
    )
    # PRZY DODAWANIU CHMURY TRZEBA DODAĆ TE POLE
    # result_file = models.FileField(upload_to="medical/%Y/", null=True, blank=True)

    class Meta:
        verbose_name = "Wpis medyczny"
        verbose_name_plural = "Wpisy medyczne"
        constraints = [
            models.CheckConstraint(  # Dodaj 'models.' tutaj
                condition=(
                        models.Q(dog__isnull=False, puppy__isnull=True, litter__isnull=True) |
                        models.Q(dog__isnull=True, puppy__isnull=False, litter__isnull=True) |
                        models.Q(dog__isnull=True, puppy__isnull=True, litter__isnull=False)
                ),
                name="medical_record_one_animal_source",
            )
        ]

    def clean(self):
        sources = [self.dog, self.puppy, self.litter]
        selected_count = sum(bool(source) for source in sources)

        if selected_count == 0:
            raise ValidationError("Musisz wybrać psa, szczeniaka LUB miot.")
        if selected_count > 1:
            raise ValidationError("Dokument może być przypisany tylko do jednego źródła naraz.")

    def __str__(self):
        if self.dog:
            return f"{self.dog}: {self.treatment_type},{self.result}"
        if self.puppy:
            return f"{self.puppy}: {self.treatment_type},{self.result}"
        return f"{self.litter}: {self.treatment_type},{self.result}"


class DocumentRecord(models.Model):
    class Category(models.TextChoices):
        PEDIGREE = "pedigree", "Rodowód"
        CONTRACT = "contract", "Umowa"
        CERTIFICATE = "certificate", "Certyfikat/Dyplom"
        OTHER = "other", "Inne"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Ostatnia edycja")
    dog = models.ForeignKey(
        "kennel.Dog",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="Pies z naszych psów",
    )
    puppy = models.ForeignKey(
        "kennel.Puppy",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="Szczenię",
    )
    litter = models.ForeignKey(
        'kennel.Litter',
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name="Miot",
    )
    date = models.DateField(blank=True, null=True, verbose_name="Data dokumentu")

    category = models.CharField(
        max_length=20,
        choices=Category.choices, #type:ignore
        default=Category.OTHER,
        verbose_name="Typ dokumentu"
    )

    document_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Nazwa dokumentu")
    # PRZY DODAWANIU CHMURY TRZEBA DODAĆ TE POLE
    # document_file = models.FileField(upload_to="document/%Y/", null=True, blank=True)

    class Meta:
        verbose_name = "Dokument"
        verbose_name_plural = "Dokumenty"
        constraints = [
            models.CheckConstraint(  # Dodaj 'models.' tutaj
                condition=(
                        models.Q(dog__isnull=False, puppy__isnull=True, litter__isnull=True) |
                        models.Q(dog__isnull=True, puppy__isnull=False, litter__isnull=True) |
                        models.Q(dog__isnull=True, puppy__isnull=True, litter__isnull=False)
                ),
                name="document_record_one_animal_source",
            )
        ]

    def clean(self):
        sources = [self.dog, self.puppy, self.litter]
        selected_count = sum(bool(source) for source in sources)

        if selected_count == 0:
            raise ValidationError("Musisz wybrać psa, szczeniaka LUB miot.")
        if selected_count > 1:
            raise ValidationError("Dokument może być przypisany tylko do jednego źródła naraz.")

    def __str__(self):
        if self.dog:
            return f"{self.dog}: {self.category} - {self.document_name}"
        if self.puppy:
            return f"{self.puppy}: {self.category} - {self.document_name}"
        return f"{self.litter}: {self.category} - {self.document_name}"
