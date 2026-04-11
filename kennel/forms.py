from django import forms
from .models import Dog
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError


class DogForm(forms.ModelForm):
    class Meta:
        model = Dog
        # Usunąłem 'exclude', bo 'fields' definiuje wszystko, co ma być widoczne
        fields = [
            'name', 'gender', 'birth_date', 'breed', 'breeding_status',
            'chip_number', 'tattoo_number', 'pkr_number', 'origin_kennel',
            'father', 'mother',
            'co_owner_first_name', 'co_owner_last_name',
            'co_owner_address_line_one', 'co_owner_address_line_two',
            'co_owner_city', 'co_owner_region', 'co_owner_postal_code', 'co_owner_country'
        ]
        widgets = {
            'birth_date': forms.DateInput(format='%Y-%m-%d',attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # 1. Pobranie użytkownika i inicjalizacja formularza
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 2. STYLIZACJA: Nadanie bazowego wyglądu wszystkim polom
        input_classes = (
            "block w-full appearance-none rounded-xl border border-gray-300 px-4 py-2 "
            "text-sm text-gray-900 shadow-sm focus:border-indigo-600 focus:ring-indigo-600 "
            "transition-all placeholder:text-gray-400 bg-white"
        )
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': input_classes})

        # 3. FILTROWANIE: Ograniczenie listy rodziców do psów danego hodowcy
        if self.user:
            base_qs = Dog.objects.filter(breeder=self.user)
            self.fields['father'].queryset = base_qs.filter(gender='male')
            self.fields['mother'].queryset = base_qs.filter(gender='female')

            if self.instance and self.instance.pk:
                self.fields['father'].queryset = self.fields['father'].queryset.exclude(pk=self.instance.pk)
                self.fields['mother'].queryset = self.fields['mother'].queryset.exclude(pk=self.instance.pk)

        # 4. BLOKADA LOGICZNA: Mrożenie danych tożsamości
        if self.instance and self.instance.pk:
            # Sprawdzamy, czy pies ma już potomstwo
            has_offspring = (self.instance.father_of.exists() or
                             self.instance.mother_of.exists())

            # Sprawdzamy, czy minęło więcej niż 3 dni od utworzenia rekordu
            if self.instance.created_at:
                is_old_record = (timezone.now() - self.instance.created_at) > timedelta(days=3)
            else:
                # Jeśli nie ma daty (np. nowy rekord lub błąd importu), uznajemy, że nie jest stary
                is_old_record = False

            # Jeśli którykolwiek warunek jest spełniony -> aktywujemy blokadę
            if has_offspring or is_old_record:
                identity_fields = ['breed', 'gender', 'birth_date', 'chip_number', 'pkr_number', 'father', 'mother']

                # Klasy dla zablokowanego pola (nadpisujemy tło na szare)
                disabled_style = "!bg-gray-200 !border-gray-300 text-gray-500 cursor-not-allowed select-none opacity-80"

                for field_name in identity_fields:
                    if field_name in self.fields:
                        current_value = getattr(self.instance, field_name)
                        # Blokujemy tylko wtedy, gdy pole nie jest puste
                        if current_value not in [None, '']:
                            self.fields[field_name].disabled = True
                            curr_class = self.fields[field_name].widget.attrs.get('class', '')
                            self.fields[field_name].widget.attrs.update({
                                'class': f"{curr_class} {disabled_style}",
                                'title': 'To pole jest zablokowane ze względu na historię rekordu'
                            })

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date and birth_date > timezone.now().date():
            raise forms.ValidationError("Data urodzenia nie może być z przyszłości.")
        return birth_date

    def clean_chip_number(self):
        chip = self.cleaned_data.get('chip_number')
        if not chip:
            return chip

        # 1. Sprawdzamy długość (najpierw walidacja formatu)
        if len(str(chip)) != 15:
            raise forms.ValidationError("Numer chip musi składać się z 15 cyfr.")

        # 2. Sprawdzamy unikalność u tego hodowcy
        exists = Dog.objects.filter(
            breeder=self.user,
            chip_number=chip
        ).exclude(pk=self.instance.pk).exists()

        if exists:
            raise forms.ValidationError("Masz już psa z tym numerem chipa w swojej hodowli.")

        return chip

    def clean_tattoo_number(self):
        tattoo = self.cleaned_data.get('tattoo_number')
        if not tattoo:
            return tattoo

        if Dog.objects.filter(breeder=self.user, tattoo_number=tattoo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Masz już psa z tym numerem tatuażu.")

        return tattoo

    def clean(self):
        cleaned_data = super().clean()
        father = cleaned_data.get('father')
        mother = cleaned_data.get('mother')

        if father and father.gender != 'male':
            self.add_error('father', "Ojcem może być wyłącznie samiec.")

        if mother and mother.gender != 'female':
            self.add_error('mother', "Matką może być wyłącznie samica.")

        if self.instance and self.instance.pk:
            if father and father.pk == self.instance.pk:
                self.add_error('father', "Pies nie może być swoim własnym ojcem.")
            if mother and mother.pk == self.instance.pk:
                self.add_error('mother', "Pies nie może być swoją własną matką.")

        return cleaned_data