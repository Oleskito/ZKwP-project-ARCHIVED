from django import forms
from .models import Dog, Litter, Puppy, Measurement
from django.utils import timezone
from datetime import timedelta


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
            'co_owner_city', 'co_owner_region', 'co_owner_postal_code', 'co_owner_country', 'profile_picture'
        ]
        widgets = {
            'birth_date': forms.DateInput(format='%Y-%m-%d',attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # 1. Pobranie użytkownika i inicjalizacja formularza
        self.user = kwargs.pop('user', None)
        self.promote_puppy_id = kwargs.pop('promote_puppy_id', None)
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


    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date and birth_date > timezone.now().date():
            raise forms.ValidationError("Data urodzenia nie może być z przyszłości.")
        return birth_date

    def clean_chip_number(self):
        chip = self.cleaned_data.get('chip_number')
        if not chip:
            return chip

        if len(str(chip)) != 15:
            raise forms.ValidationError("Numer chip musi składać się z 15 cyfr.")

        # 1. Sprawdzamy dorosłe psy
        dog_qs = Dog.objects.filter(breeder=self.user, chip_number=chip)
        if self.instance and self.instance.pk:
            dog_qs = dog_qs.exclude(pk=self.instance.pk)
        if dog_qs.exists():
            raise forms.ValidationError("Masz już innego dorosłego psa z tym numerem chipa w swojej hodowli.")

        # 2. Sprawdzamy szczenięta
        puppy_qs = Puppy.objects.filter(breeder=self.user, chip_number=chip)
        if self.instance and self.instance.pk:
            puppy_qs = puppy_qs.exclude(adult_dog_profile=self.instance)

        # KLUCZOWE: Wykluczamy szczeniaka, którego właśnie awansujemy!
        if getattr(self, 'promote_puppy_id', None):
            puppy_qs = puppy_qs.exclude(pk=self.promote_puppy_id)

        existing_puppy = puppy_qs.first()

        if existing_puppy:
            # Tutaj dzieje się magia UX! Zamiast blokować bez wyjaśnienia, dajemy instrukcję.
            raise forms.ValidationError(
                f"Ten chip należy do szczenięcia '{existing_puppy.name}' w Twojej hodowli. "
                "Aby uniknąć bałaganu w dokumentacji, nie dodawaj go ręcznie. "
                "Przejdź do profilu szczenięcia i użyj opcji 'Awansuj do stada'."
            )

        return chip

    def clean_tattoo_number(self):
        tattoo = self.cleaned_data.get('tattoo_number')
        if not tattoo:
            return tattoo

        dog_qs = Dog.objects.filter(breeder=self.user, tattoo_number=tattoo)
        if self.instance and self.instance.pk:
            dog_qs = dog_qs.exclude(pk=self.instance.pk)
        if dog_qs.exists():
            raise forms.ValidationError("Masz już innego dorosłego psa z tym numerem tatuażu.")

        puppy_qs = Puppy.objects.filter(breeder=self.user, tattoo_number=tattoo)
        if self.instance and self.instance.pk:
            puppy_qs = puppy_qs.exclude(adult_dog_profile=self.instance)

        if getattr(self, 'promote_puppy_id', None):
            puppy_qs = puppy_qs.exclude(pk=self.promote_puppy_id)

        existing_puppy = puppy_qs.first()

        if existing_puppy:
            # Ponownie serwujemy sprytną podpowiedź!
            raise forms.ValidationError(
                f"Ten tatuaż należy do szczenięcia '{existing_puppy.name}' w Twojej hodowli. "
                "Aby uniknąć bałaganu w dokumentacji, nie dodawaj go ręcznie. "
                "Przejdź do profilu szczenięcia i użyj opcji 'Awansuj do stada'."
            )

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


class LitterForm(forms.ModelForm):
    # Checkboxy sterujące
    is_external_mother = forms.BooleanField(required=False, label="Matka spoza hodowli")
    is_external_father = forms.BooleanField(required=False, label="Ojciec spoza hodowli")

    # Pola dla matki z zewnątrz (Zmienione na pkr_number)
    ext_mother_name = forms.CharField(required=False, label="Imię")
    ext_mother_titles = forms.CharField(required=False, label="Tytuły")
    ext_mother_pkr_number = forms.CharField(required=False, label="Nr PKR")
    ext_mother_chip = forms.CharField(required=False, label="Chip")
    ext_mother_color = forms.CharField(required=False, label="Maść")
    ext_mother_health_tests = forms.CharField(required=False, label="Badania")
    ext_mother_owner = forms.CharField(required=False, label="Właściciel")

    # Pola dla ojca z zewnątrz (Zmienione na pkr_number)
    ext_father_name = forms.CharField(required=False, label="Imię")
    ext_father_titles = forms.CharField(required=False, label="Tytuły")
    ext_father_pkr_number = forms.CharField(required=False, label="Nr PKR")
    ext_father_chip = forms.CharField(required=False, label="Chip")
    ext_father_color = forms.CharField(required=False, label="Maść")
    ext_father_health_tests = forms.CharField(required=False, label="Badania")
    ext_father_owner = forms.CharField(required=False, label="Właściciel")

    class Meta:
        model = Litter
        fields = [
            'litter_letter', 'status', 'breed',
            'mother', 'father',
            'mating_place', 'mating_date_start', 'mating_date_end', 'birth_date',
            'males_count', 'females_count', 'deceased_count', 'cover_photo'
        ]
        widgets = {
            'mating_date_start': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'mating_date_end': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'birth_date': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self._errors = None
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 1. STYLIZACJA
        input_classes = (
            "block w-full appearance-none rounded-xl border border-gray-300 px-4 py-2 "
            "text-sm text-gray-900 shadow-sm focus:border-indigo-600 focus:ring-indigo-600 "
            "transition-all placeholder:text-gray-400 bg-white"
        )
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': input_classes})

        # 2. FILTROWANIE
        if self.user:
            base_qs = Dog.objects.filter(breeder=self.user)
            self.fields['father'].queryset = base_qs.filter(gender='male')
            self.fields['mother'].queryset = base_qs.filter(gender='female')

        # 3. WYMAGANE POLA
        self.fields['litter_letter'].required = True
        self.fields['status'].required = True
        self.fields['breed'].required = True
        self.fields['males_count'].min_value = 0
        self.fields['females_count'].min_value = 0
        self.fields['deceased_count'].min_value = 0

        # 4. ŁADOWANIE DANYCH DLA EDYCJI
        if self.instance and self.instance.pk:
            # Matka z zewnątrz
            if self.instance.mother_data_snapshot:
                self.fields['is_external_mother'].initial = True
                self.fields['ext_mother_name'].initial = self.instance.mother_data_snapshot.get('name', '')
                self.fields['ext_mother_titles'].initial = self.instance.mother_data_snapshot.get('titles', '')
                self.fields['ext_mother_pkr_number'].initial = self.instance.mother_data_snapshot.get('pkr_number', '')
                self.fields['ext_mother_chip'].initial = self.instance.mother_data_snapshot.get('chip', '')
                self.fields['ext_mother_color'].initial = self.instance.mother_data_snapshot.get('color', '')
                self.fields['ext_mother_health_tests'].initial = self.instance.mother_data_snapshot.get('health_tests',
                                                                                                        '')
                self.fields['ext_mother_owner'].initial = self.instance.mother_data_snapshot.get('owner', '')

            # Ojciec z zewnątrz
            if self.instance.father_data_snapshot:
                self.fields['is_external_father'].initial = True
                self.fields['ext_father_name'].initial = self.instance.father_data_snapshot.get('name', '')
                self.fields['ext_father_titles'].initial = self.instance.father_data_snapshot.get('titles', '')
                self.fields['ext_father_pkr_number'].initial = self.instance.father_data_snapshot.get('pkr_number', '')
                self.fields['ext_father_chip'].initial = self.instance.father_data_snapshot.get('chip', '')
                self.fields['ext_father_color'].initial = self.instance.father_data_snapshot.get('color', '')
                self.fields['ext_father_health_tests'].initial = self.instance.father_data_snapshot.get('health_tests',
                                                                                                        '')
                self.fields['ext_father_owner'].initial = self.instance.father_data_snapshot.get('owner', '')


    def clean(self):
        cleaned_data = super().clean()
        is_ext_mother = cleaned_data.get('is_external_mother', False)
        is_ext_father = cleaned_data.get('is_external_father', False)

        # Logika dla Matki (POPRAWIONE WCIĘCIA)
        if is_ext_mother:
            if 'mother' in self._errors:
                self._errors.pop('mother')

            # Kod na zewnątrz if _errors
            ext_name = cleaned_data.get('ext_mother_name')
            if not ext_name:
                self.add_error('ext_mother_name', "Podaj przynajmniej imię matki z zewnątrz.")

            mother_data = {
                'name': ext_name,
                'titles': cleaned_data.get('ext_mother_titles'),
                'pkr_number': cleaned_data.get('ext_mother_pkr_number'),
                'chip': cleaned_data.get('ext_mother_chip'),
                'color': cleaned_data.get('ext_mother_color'),
                'health_tests': cleaned_data.get('ext_mother_health_tests'),
                'owner': cleaned_data.get('ext_mother_owner'),
            }
            self.instance.mother_data_snapshot = {k: v for k, v in mother_data.items() if v}
            cleaned_data['mother'] = None
        else:
            self.instance.mother_data_snapshot = {}

        # Logika dla Ojca (POPRAWIONE WCIĘCIA)
        if is_ext_father:
            if 'father' in self._errors:
                self._errors.pop('father')

            ext_name = cleaned_data.get('ext_father_name')
            if not ext_name:
                self.add_error('ext_father_name', "Podaj przynajmniej imię ojca z zewnątrz.")

            father_data = {
                'name': ext_name,
                'titles': cleaned_data.get('ext_father_titles'),
                'pkr_number': cleaned_data.get('ext_father_pkr_number'),
                'chip': cleaned_data.get('ext_father_chip'),
                'color': cleaned_data.get('ext_father_color'),
                'health_tests': cleaned_data.get('ext_father_health_tests'),
                'owner': cleaned_data.get('ext_father_owner'),
            }
            self.instance.father_data_snapshot = {k: v for k, v in father_data.items() if v}
            cleaned_data['father'] = None
        else:
            self.instance.father_data_snapshot = {}

        status = cleaned_data.get('status')
        birth_date = cleaned_data.get('birth_date')
        males = cleaned_data.get('males_count') or 0
        females = cleaned_data.get('females_count') or 0
        deceased = cleaned_data.get('deceased_count') or 0

        total_puppies = males + females + deceased

        status_labels = {
            'planned': 'Planowany',
            'mating': 'Krycie wykonane',
            'not_pregnant': 'Brak ciąży',
            'born': 'Urodzone',
            'registered': 'Zgłoszony',
            'inspected': 'Po przeglądzie',
            'archived': 'Archiwum'
        }
        readable_status = status_labels.get(status, status)
        statuses_pre_birth = ['planned', 'mating', 'not_pregnant']

        mating_start = cleaned_data.get('mating_date_start')
        mating_end = cleaned_data.get('mating_date_end')
        birth_date = cleaned_data.get('birth_date')

        if mating_start and mating_end and mating_start > mating_end:
            self.add_error('mating_date_start', "Data rozpoczęcia krycia nie może być późniejsza niż data zakończenia.")

        if birth_date:
            if mating_start and mating_start > birth_date:
                self.add_error('birth_date', "Narodziny nie mogą nastąpić przed rozpoczęciem krycia.")
            if mating_end and mating_end > birth_date:
                self.add_error('birth_date', "Narodziny nie mogą nastąpić przed zakończeniem krycia.")

        if status in statuses_pre_birth:
            if birth_date:
                self.add_error('birth_date', f'Mioty o statusie "{readable_status}" nie mogą mieć daty narodzin.')
            if total_puppies > 0:
                self.add_error('status', f'Nie możesz przypisać szczeniąt do miotu o statusie "{readable_status}".')

        statuses_post_birth = ['born', 'registered', 'inspected',]

        if status in statuses_post_birth:
            if not birth_date:
                self.add_error('birth_date', f'Miot o statusie "{readable_status}" musi mieć podaną datę narodzin.')
            if total_puppies == 0:
                self.add_error('status', f'Miot o statusie "{readable_status}" musi mieć przypisane szczenięta.')

        return cleaned_data


class PuppyForm(forms.ModelForm):
    class Meta:
        model = Puppy
        fields = ['litter', 'name', 'gender', 'color', 'internal_id', 'chip_number', 'tattoo_number', 'status', 'profile_picture']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # STYLIZACJA
        input_classes = (
            "block w-full appearance-none rounded-xl border border-gray-300 px-4 py-2 "
            "text-sm text-gray-900 shadow-sm focus:border-indigo-600 focus:ring-indigo-600 "
            "transition-all placeholder:text-gray-400 bg-white"
        )
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': input_classes})

        # FILTROWANIE - Hodowca widzi w formularzu tylko SWOJE mioty
        if self.user:
            self.fields['litter'].queryset = Litter.objects.filter(breeder=self.user).order_by('-created_at')

        if self.instance and self.instance.pk and hasattr(self.instance,
                                                          'adult_dog_profile') and self.instance.adult_dog_profile:
            locked_fields = ['chip_number', 'tattoo_number', 'gender', 'name', 'color']
            for field in locked_fields:
                if field in self.fields:
                    self.fields[field].disabled = True
                    self.fields[field].widget.attrs['class'] += " bg-gray-100 text-gray-500 cursor-not-allowed"
                    self.fields[field].help_text = "Zablokowane (szczenię awansowane do stada)."

    def clean_chip_number(self):
        chip = self.cleaned_data.get('chip_number')
        if not chip:
            return chip

        # 1. Walidacja formatu (15 cyfr)
        if len(str(chip)) != 15:
            raise forms.ValidationError("Numer chip musi składać się z 15 cyfr.")

        # 2. Sprawdzamy unikalność u tego hodowcy (szukamy w psach i szczeniętach)
        exists_in_dogs = Dog.objects.filter(breeder=self.user, chip_number=chip).exists()
        exists_in_puppies = Puppy.objects.filter(breeder=self.user, chip_number=chip).exclude(pk=self.instance.pk).exists()

        if exists_in_dogs or exists_in_puppies:
            raise forms.ValidationError("Masz już zwierzę z tym numerem chipa w swojej hodowli.")

        return chip

    def clean_tattoo_number(self):
        tattoo = self.cleaned_data.get('tattoo_number')
        if not tattoo:
            return tattoo

        exists_in_dogs = Dog.objects.filter(breeder=self.user, tattoo_number=tattoo).exists()
        exists_in_puppies = Puppy.objects.filter(breeder=self.user, tattoo_number=tattoo).exclude(pk=self.instance.pk).exists()

        if exists_in_dogs or exists_in_puppies:
            raise forms.ValidationError("Masz już zwierzę z tym numerem tatuażu.")

        return tattoo


class MeasurementForm(forms.ModelForm):
    class Meta:
        model = Measurement
        fields = ['date', 'weight', 'height', 'chest_girth', 'head_girth', 'body_length', 'temperature', 'bcs', 'photo', 'notes']

        # Określamy dokładne typy inputów i ich atrybuty (krok ułamkowy i format daty)
        widgets = {
            'date': forms.DateInput(
                format='%Y-%m-%d',  # To naprawia znikającą datę przy edycji!
                attrs={'type': 'date'}
            ),
            'weight': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'height': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'chest_girth': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'head_girth': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'body_length': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'temperature': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
            'bcs': forms.NumberInput(attrs={'step': '1', 'min': '1', 'max': '9'}),  # Skala BCS od 1 do 9
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # 1. Przechwytujemy psa lub szczeniaka z widoku
        self.dog = kwargs.pop('dog', None)
        self.puppy = kwargs.pop('puppy', None)

        super().__init__(*args, **kwargs)

        # 2. Wstrzykujemy zwierzaka do instancji PRZED walidacją
        # Dzięki temu model.clean() przestanie blokować zapis!
        if self.dog:
            self.instance.dog = self.dog
        if self.puppy:
            self.instance.puppy = self.puppy

        # BAZOWA STYLIZACJA DLA WSZYSTKICH INPUTÓW POMIARÓW
        input_classes = (
            "block w-full appearance-none rounded-lg border border-gray-200 px-3 py-2.5 "
            "text-base lg:text-xs text-gray-900 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 "
            "transition-all placeholder:text-gray-400 bg-white outline-none"
        )

        # Pętla przypisująca klasę Tailwind do każdego pola
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f"{current_class} {input_classes}".strip()