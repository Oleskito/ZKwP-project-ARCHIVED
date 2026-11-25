import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from .models import (
    Dog,
    Litter,
    Puppy,
    Measurement,
    MedicalRecord,
    TreatmentType,
    TreatmentResult,
    DocumentRecord,
)
from django.db.models import Q
from .forms import (
    DogForm,
    LitterForm,
    PuppyForm,
    MeasurementForm,
    MedicalRecordForm,
    DocumentRecordForm,
)
from django.contrib import messages
from django.utils import timezone


@login_required
def dashboard_view(request):
    breeder = request.user
    active_dogs_count = Dog.objects.filter(
        breeder=breeder, breeding_status=Dog.BreedingStatus.ACTIVE
    ).count()

    available_puppies_count = Puppy.objects.filter(
        breeder=breeder, status=Puppy.Status.AVAILABLE
    ).count()

    active_litters_count = Litter.objects.filter(
        breeder=breeder,
        status__in=[
            Litter.Status.BORN,
            Litter.Status.REPORTED,
            Litter.Status.INSPECTED,
        ],
    ).count()

    expected_litters_count = Litter.objects.filter(
        breeder=breeder, status__in=[Litter.Status.PLANNED, Litter.Status.MATED]
    ).count()

    context = {
        "active_dogs_count": active_dogs_count,
        "available_puppies_count": available_puppies_count,
        "active_litters_count": active_litters_count,
        "expected_litters_count": expected_litters_count,
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
def dashboard_dog_view(request):
    breeder = request.user
    active_tab = request.GET.get("tab", "active")

    q = request.GET.get("q", "").strip()
    selected_genders = request.GET.getlist("gender")
    selected_breeds = request.GET.getlist("breed")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    selected_statuses = request.GET.getlist("status")
    sort_by = request.GET.get("sort", "name_asc")

    # Bazy całkowite (do licznika "w tle")
    total_active_base = Dog.objects.filter(
        breeder=breeder, is_archived=False
    ).select_related("breed")
    total_archived_base = Dog.objects.filter(
        breeder=breeder, is_archived=True
    ).select_related("breed")

    # Izolacja - filtrujemy tylko tę bazę, w której jesteśmy
    if active_tab == "active":
        current_qs = total_active_base
        available_breeds = (
            total_active_base.exclude(breed__isnull=True)
            .values_list("breed__name", flat=True)
            .distinct()
        )
    else:
        current_qs = total_archived_base
        available_breeds = (
            total_archived_base.exclude(breed__isnull=True)
            .values_list("breed__name", flat=True)
            .distinct()
        )

    # Aplikowanie filtrów (tylko do current_qs!)
    if q:
        current_qs = current_qs.filter(
            Q(name__icontains=q)
            | Q(chip_number__icontains=q)
            | Q(tattoo_number__icontains=q)
            | Q(pkr_number__icontains=q)
        )
    if selected_genders:
        current_qs = current_qs.filter(gender__in=selected_genders)
    if selected_breeds:
        current_qs = current_qs.filter(breed__name__in=selected_breeds)
    if date_from:
        current_qs = current_qs.filter(birth_date__gte=date_from)
    if date_to:
        current_qs = current_qs.filter(birth_date__lte=date_to)
    if selected_statuses:
        current_qs = current_qs.filter(breeding_status__in=selected_statuses)

    sort_mapping = {
        "name_asc": "name",
        "name_desc": "-name",
        "date_desc": "-birth_date",
        "date_asc": "birth_date",
    }
    sort_field = sort_mapping.get(sort_by, "name")
    current_qs = current_qs.order_by(sort_field)

    # Obliczanie liczników i wysyłanie list
    if active_tab == "active":
        active_count = current_qs.count()  # Zmienny licznik
        archived_count = total_archived_base.count()  # Stały licznik w tle
        active_dogs = current_qs
        archived_dogs = Dog.objects.none()
    else:
        active_count = total_active_base.count()  # Stały licznik w tle
        archived_count = current_qs.count()  # Zmienny licznik
        active_dogs = Dog.objects.none()
        archived_dogs = current_qs

    context = {
        "active_dogs": active_dogs,
        "archived_dogs": archived_dogs,
        "active_count": active_count,
        "archived_count": archived_count,
        "available_breeds": available_breeds,
        "current_q": q,
        "current_genders": selected_genders,
        "current_breeds": selected_breeds,
        "current_statuses": selected_statuses,
        "current_date_from": date_from,
        "current_date_to": date_to,
        "current_sort": sort_by,
        "active_tab": active_tab,
    }
    return render(request, "dashboard_dog/dashboard_dog.html", context)


@login_required
def dog_add_view(request):
    user_kennel = request.user.kennel_name or "NIEUSTAWIONY PRZYDOMEK"

    puppy_id = request.GET.get("promote_puppy")
    puppy_to_promote = None
    if puppy_id:
        puppy_to_promote = get_object_or_404(Puppy, pk=puppy_id, breeder=request.user)
        # Zabezpieczenie przed ponownym awansem
        if (
            hasattr(puppy_to_promote, "adult_dog_profile")
            and puppy_to_promote.adult_dog_profile
        ):
            messages.warning(
                request,
                f"Szczenię {puppy_to_promote.name} jest już w dorosłym stadzie!",
            )
            return redirect("dashboard_puppy")

    if request.method == "POST":
        # Przekazujemy ID szczeniaka, by pominąć blokadę powielonego chipa
        promote_id = puppy_to_promote.pk if puppy_to_promote else None
        form = DogForm(
            request.POST, request.FILES, user=request.user, promote_puppy_id=promote_id
        )

        if form.is_valid():
            dog = form.save(commit=False)
            dog.breeder = request.user
            dog.save()

            # MAGIA AWANSU: Most w bazie danych
            if puppy_to_promote:
                puppy_to_promote.adult_dog_profile = dog
                puppy_to_promote.status = "staying"  # Zmienia status w miocie
                puppy_to_promote.save()
                messages.success(
                    request, f"Pomyślnie awansowano szczenię {dog.name} do stada!"
                )
            else:
                messages.success(request, f"Pomyślnie dodano psa {dog.name}!")

            return redirect("dashboard_dog")
    else:
        # Wstępne wypełnienie formularza danymi malucha
        initial_data = {}
        if puppy_to_promote:
            initial_data = {
                "name": puppy_to_promote.name,
                "gender": puppy_to_promote.gender,
                "chip_number": puppy_to_promote.chip_number,
                "tattoo_number": puppy_to_promote.tattoo_number,
                "birth_date": puppy_to_promote.litter.birth_date
                if puppy_to_promote.litter
                else None,
                "breed": puppy_to_promote.litter.breed
                if puppy_to_promote.litter
                else None,
                "mother": puppy_to_promote.litter.mother
                if puppy_to_promote.litter
                else None,
                "father": puppy_to_promote.litter.father
                if puppy_to_promote.litter
                else None,
            }
            messages.info(
                request,
                f"Formularz skopiował podstawowe dane szczenięcia {puppy_to_promote.name}.",
            )

        form = DogForm(user=request.user, initial=initial_data)

    return render(
        request,
        "dashboard_dog/dashboard_dog_add.html",
        {"form": form, "user_kennel": user_kennel},
    )


@login_required
def dog_delete_view(request, pk):
    dog = get_object_or_404(Dog, pk=pk, breeder=request.user)

    if request.method == "POST":
        # COFNIĘCIE AWANSU: Gdy usuwamy psa, szczeniak znów staje się dostępny
        if hasattr(dog, "original_puppy") and dog.original_puppy:
            puppy = dog.original_puppy
            puppy.status = "available"
            puppy.save()

        name = dog.name
        dog.delete()
        messages.success(request, f"Pomyślnie usunięto psa {name}!")
        return redirect("dashboard_dog")

    return render(
        request, "dashboard_dog/dashboard_dog_confirm_delete.html", {"dog": dog}
    )


@login_required
def dog_edit_view(request, pk):
    # Pobieramy konkretnego psa, pilnując, by należał do zalogowanego hodowcy
    dog = get_object_or_404(Dog, pk=pk, breeder=request.user)

    if request.method == "POST":
        # Kluczowe: przekazujemy 'instance=dog', żeby Django wiedziało,
        # że edytujemy istniejący rekord, a nie tworzymy nowy.
        form = DogForm(request.POST, request.FILES, instance=dog, user=request.user)

        if form.is_valid():
            form.save()  # Metoda save() w modelu automatycznie zadba o is_archived
            messages.success(request, f"Pomyślnie zaktualizowano psa {dog.name}!")
            return redirect("dashboard_dog")
        else:
            print(form.errors)
    else:
        # GET: Formularz wypełniony danymi psa
        form = DogForm(instance=dog, user=request.user)

    return render(
        request, "dashboard_dog/dashboard_dog_edit.html", {"form": form, "dog": dog}
    )


@login_required
def dashboard_litter_view(request):
    breeder = request.user
    active_tab = request.GET.get("tab", "active")

    q = request.GET.get("q", "").strip()
    selected_statuses = request.GET.getlist("status")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    mating_date_from = request.GET.get("mating_date_from")
    mating_date_to = request.GET.get("mating_date_to")
    sort_by = request.GET.get("sort", "date_desc")

    total_active_base = (
        Litter.objects.filter(breeder=breeder)
        .exclude(status=Litter.Status.ARCHIVED)
        .select_related("mother", "father", "breed")
    )
    total_archived_base = Litter.objects.filter(
        breeder=breeder, status=Litter.Status.ARCHIVED
    ).select_related("mother", "father", "breed")

    if active_tab == "active":
        current_qs = total_active_base
    else:
        current_qs = total_archived_base

    if q:
        current_qs = current_qs.filter(litter_letter__icontains=q)
    if date_from:
        current_qs = current_qs.filter(birth_date__gte=date_from)
    if date_to:
        current_qs = current_qs.filter(birth_date__lte=date_to)
    if mating_date_from:
        current_qs = current_qs.filter(mating_date_start__gte=mating_date_from)
    if mating_date_to:
        current_qs = current_qs.filter(mating_date_start__lte=mating_date_to)
    if selected_statuses:
        current_qs = current_qs.filter(status__in=selected_statuses)

    sort_mapping = {
        "date_desc": "-birth_date",
        "date_asc": "birth_date",
        "letter_asc": "litter_letter",
        "letter_desc": "-litter_letter",
    }
    sort_field = sort_mapping.get(sort_by, "-birth_date")
    current_qs = current_qs.order_by(sort_field)

    if active_tab == "active":
        active_count = current_qs.count()
        archived_count = total_archived_base.count()
        active_litters = current_qs
        archived_litters = Litter.objects.none()
    else:
        active_count = total_active_base.count()
        archived_count = current_qs.count()
        active_litters = Litter.objects.none()
        archived_litters = current_qs

    context = {
        "active_litters": active_litters,
        "archived_litters": archived_litters,
        "active_count": active_count,
        "archived_count": archived_count,
        "current_q": q,
        "current_statuses": selected_statuses,
        "current_date_from": date_from,
        "current_date_to": date_to,
        "current_sort": sort_by,
        "active_tab": active_tab,
        "current_mating_date_from": mating_date_from,
        "current_mating_date_to": mating_date_to,
    }
    return render(request, "dashboard_litter/dashboard_litter.html", context)


@login_required
def litter_add_view(request):
    if request.method == "POST":
        form = LitterForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            litter = form.save(commit=False)
            litter.breeder = request.user
            litter.save()
            messages.success(
                request, f"Pomyślnie dodano miot {litter.litter_letter or ''}!"
            )
            return redirect(
                "dashboard_litter"
            )  # Upewnij się, że tak nazywa się Twój url dla listy miotów
    else:
        form = LitterForm(user=request.user)

    return render(request, "dashboard_litter/dashboard_litter_add.html", {"form": form})


@login_required
def litter_edit_view(request, pk):
    # Pobieramy miot, upewniając się, że należy do zalogowanego hodowcy
    litter = get_object_or_404(Litter, pk=pk, breeder=request.user)

    if request.method == "POST":
        # Przekazujemy instance=litter, by Django wiedziało, że edytujemy, a nie tworzymy nowy!
        form = LitterForm(
            request.POST, request.FILES, instance=litter, user=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(
                request, f"Pomyślnie zaktualizowano miot {litter.litter_letter or ''}!"
            )
            return redirect("dashboard_litter")
    else:
        # GET: Wypełniamy formularz danymi z bazy
        form = LitterForm(instance=litter, user=request.user)

    return render(
        request,
        "dashboard_litter/dashboard_litter_edit.html",
        {"form": form, "litter": litter},
    )


@login_required
def litter_delete_view(request, pk):
    # Pobieramy miot i upewniamy się, że należy do aktualnie zalogowanego użytkownika
    litter = get_object_or_404(Litter, pk=pk, breeder=request.user)

    if request.method == "POST":
        # Zapisujemy literę do komunikatu, zanim usuniemy obiekt
        letter = litter.litter_letter or "bez litery"
        litter.delete()
        messages.success(request, f"Pomyślnie usunięto miot {letter}.")
        return redirect("dashboard_litter")

    return render(
        request,
        "dashboard_litter/dashboard_litter_confirm_delete.html",
        {"litter": litter},
    )


@login_required
def dashboard_puppy_view(request):
    active_tab = request.GET.get("tab", "current")

    query = request.GET.get("q", "").strip()
    genders = request.GET.getlist("gender")
    statuses = request.GET.getlist("status")
    sort_by = request.GET.get("sort", "name_asc")
    litter_id = request.GET.get("litter_id")

    # 1. BAZY CAŁKOWITE (Tło, bez włączonych filtrów)
    base_puppies = Puppy.objects.filter(breeder=request.user).select_related(
        "litter", "adult_dog_profile"
    )

    active_puppy_statuses = ["available", "reserved", "booked", "staying", "", None]
    inactive_puppy_statuses = ["sold", "deceased"]

    total_current_base = base_puppies.exclude(litter__status="archived")

    total_attention_base = base_puppies.filter(
        litter__status="archived", status__in=active_puppy_statuses
    )

    total_history_base = base_puppies.filter(
        litter__status="archived", status__in=inactive_puppy_statuses
    )

    # 2. IZOLACJA - Wybieramy bazę tylko dla aktywnej zakładki
    if active_tab == "attention":
        current_qs = total_attention_base
    elif active_tab == "history":
        current_qs = total_history_base
    else:
        current_qs = total_current_base

    # 3. APLIKOWANIE FILTRÓW (Tylko do current_qs, filtry nie uciekają!)
    if query:
        current_qs = current_qs.filter(
            Q(name__icontains=query) | Q(chip_number__icontains=query)
        )
    if litter_id:
        current_qs = current_qs.filter(litter_id=litter_id)
    if genders:
        current_qs = current_qs.filter(gender__in=genders)
    if statuses:
        current_qs = current_qs.filter(status__in=statuses)

    if sort_by == "name_asc":
        current_qs = current_qs.order_by("name")
    elif sort_by == "name_desc":
        current_qs = current_qs.order_by("-name")
    else:
        current_qs = current_qs.order_by("-created_at")

    # 4. OBLICZANIE LICZNIKÓW I ROZDZIAŁ DANYCH
    current_count = total_current_base.count()
    attention_count = total_attention_base.count()
    history_count = total_history_base.count()

    current_puppies = Puppy.objects.none()
    attention_puppies = Puppy.objects.none()
    history_puppies = Puppy.objects.none()

    if active_tab == "attention":
        attention_puppies = current_qs
        attention_count = current_qs.count()  # Aktualizujemy licznik po filtrach
    elif active_tab == "history":
        history_puppies = current_qs
        history_count = current_qs.count()  # Aktualizujemy licznik po filtrach
    else:
        current_puppies = current_qs
        current_count = current_qs.count()  # Aktualizujemy licznik po filtrach

    # Mioty dla dropdowna z filtrowaniem - izolowane
    if active_tab == "current":
        user_litters = (
            Litter.objects.filter(breeder=request.user)
            .exclude(status="archived")
            .order_by("-created_at")
        )
    else:
        user_litters = Litter.objects.filter(
            breeder=request.user, status="archived"
        ).order_by("-created_at")

    context = {
        "active_tab": active_tab,
        "current_puppies": current_puppies,
        "attention_puppies": attention_puppies,
        "history_puppies": history_puppies,
        # PRZESYŁAMY LICZNIKI
        "current_count": current_count,
        "attention_count": attention_count,
        "history_count": history_count,
        "user_litters": user_litters,
        "current_q": query,
        "current_genders": genders,
        "current_statuses": statuses,
        "current_sort": sort_by,
        "current_litter_id": litter_id,
    }

    return render(request, "dashboard_puppy/dashboard_puppy.html", context)


@login_required
def puppy_add_view(request):
    if request.method == "POST":
        # Przekazujemy user do formularza (nawet jeśli na razie nie ma walidacji, przyda się za chwilę)
        form = PuppyForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            puppy = form.save(commit=False)
            puppy.breeder = request.user
            puppy.save()
            messages.success(request, f"Pomyślnie dodano szczenię {puppy.name}!")
            return redirect("dashboard_puppy")  # Upewnij się, że masz ten URL w urls.py
    else:
        form = PuppyForm(user=request.user)

    return render(request, "dashboard_puppy/dashboard_puppy_add.html", {"form": form})


@login_required
def puppy_edit_view(request, pk):
    # Pobieramy szczenię, upewniając się, że należy do zalogowanego hodowcy
    puppy = get_object_or_404(Puppy, pk=pk, breeder=request.user)

    if request.method == "POST":
        form = PuppyForm(request.POST, request.FILES, instance=puppy, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Pomyślnie zaktualizowano dane szczenięcia {puppy.name}!"
            )
            return redirect("dashboard_puppy")
    else:
        form = PuppyForm(instance=puppy, user=request.user)

    return render(
        request,
        "dashboard_puppy/dashboard_puppy_edit.html",
        {"form": form, "puppy": puppy},
    )


@login_required
def puppy_delete_view(request, pk):
    puppy = get_object_or_404(Puppy, pk=pk, breeder=request.user)

    if request.method == "POST":
        # ZABEZPIECZENIE: Nie wolno usunąć szczeniaka, jeśli jest dorosły
        if hasattr(puppy, "adult_dog_profile") and puppy.adult_dog_profile:
            messages.error(
                request,
                f"Nie możesz usunąć szczenięcia {puppy.name}, ponieważ figuruje jako dorosły pies w stadzie. Najpierw usuń dorosłego psa.",
            )
            return redirect("dashboard_puppy")

        name = puppy.name
        puppy.delete()
        messages.success(request, f"Pomyślnie usunięto szczenię {name}.")
        return redirect("dashboard_puppy")

    return render(
        request, "dashboard_puppy/dashboard_puppy_confirm_delete.html", {"puppy": puppy}
    )


@login_required
def dog_measurements_view(request, pk):
    dog = get_object_or_404(Dog, pk=pk, breeder=request.user)

    # MAGIA POŁĄCZENIA: Pobieramy pomiary dorosłego psa ORAZ te ze szczenięctwa
    if hasattr(dog, "original_puppy") and dog.original_puppy:
        measurements = (
            Measurement.objects.filter(Q(dog=dog) | Q(puppy=dog.original_puppy))
            .select_related("dog", "puppy")
            .order_by("-date", "-created_at")
        )
    else:
        measurements = (
            Measurement.objects.filter(dog=dog)
            .select_related("dog")
            .order_by("-date", "-created_at")
        )

    if request.method == "POST":
        form = MeasurementForm(request.POST, request.FILES, dog=dog)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Pomyślnie dodano nowy pomiar dla psa {dog.name}."
            )
            return redirect("dog_measurements", pk=dog.pk)
    else:
        form = MeasurementForm(initial={"date": timezone.now().date()})

    context = {"dog": dog, "measurements": measurements, "form": form}
    return render(request, "dashboard_dog/dashboard_dog_measurements.html", context)


@login_required
def puppy_measurements_view(request, pk):
    puppy = get_object_or_404(Puppy, pk=pk, breeder=request.user)
    measurements = (
        Measurement.objects.filter(puppy=puppy)
        .select_related("puppy")
        .order_by("-date", "-created_at")
    )

    if request.method == "POST":
        # TUTAJ ZMIANA: Przekazujemy puppy=puppy do formularza
        form = MeasurementForm(request.POST, request.FILES, puppy=puppy)
        if form.is_valid():
            form.save()  # TUTAJ ZMIANA
            messages.success(request, f"Pomyślnie dodano pomiar dla {puppy.name}.")
            return redirect("puppy_measurements", pk=puppy.pk)
    else:
        form = MeasurementForm(initial={"date": timezone.now().date()})

    context = {"puppy": puppy, "measurements": measurements, "form": form}
    return render(request, "dashboard_puppy/dashboard_puppy_measurements.html", context)


@login_required
def measurement_edit_view(request, pk):
    measurement = get_object_or_404(
        Measurement.objects.select_related(
            "dog__breeder", "puppy__breeder", "puppy__adult_dog_profile"
        ),
        pk=pk,
    )
    owner = measurement.dog or measurement.puppy
    if owner is None or owner.breeder != request.user:
        messages.error(request, "Brak uprawnień.")
        return redirect("dashboard")

    if request.method == "POST":
        form = MeasurementForm(request.POST, request.FILES, instance=measurement)
        if form.is_valid():
            form.save()
            messages.success(request, "Pomyślnie zaktualizowano pomiar.")
            if measurement.dog:
                return redirect("dog_measurements", pk=measurement.dog.pk)
            if measurement.puppy.adult_dog_profile:
                return redirect(
                    "dog_measurements", pk=measurement.puppy.adult_dog_profile.pk
                )
            return redirect("puppy_measurements", pk=measurement.puppy.pk)
    else:
        form = MeasurementForm(instance=measurement)

    animal = measurement.dog or measurement.puppy
    context = {
        "form": form,
        "animal_name": animal.name,
        "animal_pk": animal.pk,
        "is_dog": measurement.dog is not None,
        "measurement": measurement,
    }
    return render(request, "dashboard/measurement_edit.html", context)


@login_required
def measurement_delete_view(request, pk):
    measurement = get_object_or_404(
        Measurement.objects.select_related(
            "dog__breeder", "puppy__breeder", "puppy__adult_dog_profile"
        ),
        pk=pk,
    )
    owner = measurement.dog or measurement.puppy
    if owner is None or owner.breeder != request.user:
        messages.error(request, "Brak uprawnień.")
        return redirect("dashboard")

    if measurement.dog:
        back_url_name = "dog_measurements"
        back_pk = measurement.dog.pk
    elif measurement.puppy.adult_dog_profile:
        back_url_name = "dog_measurements"
        back_pk = measurement.puppy.adult_dog_profile.pk
    else:
        back_url_name = "puppy_measurements"
        back_pk = measurement.puppy.pk

    if request.method == "POST":
        measurement.delete()
        messages.success(request, "Pomyślnie usunięto pomiar.")
        return redirect(back_url_name, pk=back_pk)

    return render(
        request,
        "dashboard/measurement_confirm_delete.html",
        {
            "measurement": measurement,
            "back_url_name": back_url_name,
            "back_pk": back_pk,
        },
    )


def _breeder_medical_qs(user):
    return MedicalRecord.objects.filter(
        Q(dog__breeder=user) | Q(puppy__breeder=user) | Q(litter__breeder=user)
    ).select_related("treatment_type", "result", "dog", "puppy", "litter")


@login_required
def dashboard_medical_view(request):
    breeder = request.user
    q = request.GET.get("q", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    selected_type_ids = request.GET.getlist("treatment_type")
    sort_by = request.GET.get("sort", "newest")

    records = _breeder_medical_qs(breeder)

    if q:
        records = records.filter(
            Q(dog__name__icontains=q)
            | Q(puppy__name__icontains=q)
            | Q(litter__litter_letter__icontains=q)
        )
    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    if selected_type_ids:
        records = records.filter(treatment_type__id__in=selected_type_ids)

    records = records.order_by("date" if sort_by == "oldest" else "-date")

    available_types = (
        TreatmentType.objects.filter(
            Q(medicalrecord__dog__breeder=breeder)
            | Q(medicalrecord__puppy__breeder=breeder)
            | Q(medicalrecord__litter__breeder=breeder)
        )
        .distinct()
        .order_by("name")
    )

    return render(
        request,
        "dashboard_medical/dashboard_medical.html",
        {
            "records": records,
            "current_q": q,
            "current_date_from": date_from,
            "current_date_to": date_to,
            "current_type_ids": selected_type_ids,
            "current_sort": sort_by,
            "available_types": available_types,
        },
    )


@login_required
def medical_add_view(request):
    all_results = list(
        TreatmentResult.objects.select_related("treatment_type").values(
            "id", "name", "treatment_type_id"
        )
    )
    results_json = json.dumps(
        [
            {
                "id": str(r["id"]),
                "name": r["name"],
                "type_id": str(r["treatment_type_id"]),
            }
            for r in all_results
        ]
    )

    if request.method == "POST":
        form = MedicalRecordForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Pomyślnie dodano wpis medyczny!")
            return redirect("dashboard_medical")
    else:
        form = MedicalRecordForm(user=request.user)

    return render(
        request,
        "dashboard_medical/dashboard_medical_add.html",
        {
            "form": form,
            "results_json": results_json,
        },
    )


@login_required
def medical_edit_view(request, pk):
    record = get_object_or_404(_breeder_medical_qs(request.user), pk=pk)

    all_results = list(
        TreatmentResult.objects.select_related("treatment_type").values(
            "id", "name", "treatment_type_id"
        )
    )
    results_json = json.dumps(
        [
            {
                "id": str(r["id"]),
                "name": r["name"],
                "type_id": str(r["treatment_type_id"]),
            }
            for r in all_results
        ]
    )

    if request.method == "POST":
        form = MedicalRecordForm(
            request.POST, request.FILES, instance=record, user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Pomyślnie zaktualizowano wpis medyczny!")
            return redirect("dashboard_medical")
    else:
        form = MedicalRecordForm(instance=record, user=request.user)

    return render(
        request,
        "dashboard_medical/dashboard_medical_edit.html",
        {
            "form": form,
            "record": record,
            "results_json": results_json,
        },
    )


@login_required
def medical_delete_view(request, pk):
    record = get_object_or_404(_breeder_medical_qs(request.user), pk=pk)

    if request.method == "POST":
        record.delete()
        messages.success(request, "Pomyślnie usunięto wpis medyczny.")
        return redirect("dashboard_medical")

    return render(
        request,
        "dashboard_medical/dashboard_medical_confirm_delete.html",
        {
            "record": record,
        },
    )


def _breeder_document_qs(user: object) -> object:
    return DocumentRecord.objects.filter(
        Q(dog__breeder=user) | Q(puppy__breeder=user) | Q(litter__breeder=user)
    ).select_related("dog", "puppy", "litter")


@login_required
def dashboard_documents_view(request):
    breeder = request.user
    q = request.GET.get("q", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()
    selected_categories = request.GET.getlist("category")
    sort_by = request.GET.get("sort", "newest")

    records = _breeder_document_qs(breeder)

    if q:
        records = records.filter(
            Q(dog__name__icontains=q)
            | Q(puppy__name__icontains=q)
            | Q(litter__litter_letter__icontains=q)
            | Q(document_name__icontains=q)
        )
    if date_from:
        records = records.filter(date__gte=date_from)
    if date_to:
        records = records.filter(date__lte=date_to)
    if selected_categories:
        records = records.filter(category__in=selected_categories)

    records = records.order_by(
        "date" if sort_by == "oldest" else "-date", "-created_at"
    )

    return render(
        request,
        "dashboard_documents/dashboard_documents.html",
        {
            "records": records,
            "current_q": q,
            "current_date_from": date_from,
            "current_date_to": date_to,
            "current_categories": selected_categories,
            "current_sort": sort_by,
            "category_choices": DocumentRecord.Category.choices,
        },
    )


@login_required
def document_add_view(request):
    if request.method == "POST":
        form = DocumentRecordForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Pomyślnie dodano dokument!")
            return redirect("dashboard_documents")
    else:
        form = DocumentRecordForm(user=request.user)

    return render(
        request,
        "dashboard_documents/dashboard_documents_add.html",
        {
            "form": form,
        },
    )


@login_required
def document_edit_view(request, pk):
    record = get_object_or_404(_breeder_document_qs(request.user), pk=pk)

    if request.method == "POST":
        form = DocumentRecordForm(
            request.POST, request.FILES, instance=record, user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Pomyślnie zaktualizowano dokument!")
            return redirect("dashboard_documents")
    else:
        form = DocumentRecordForm(instance=record, user=request.user)

    return render(
        request,
        "dashboard_documents/dashboard_documents_edit.html",
        {
            "form": form,
            "record": record,
        },
    )


@login_required
def document_delete_view(request, pk):
    record = get_object_or_404(_breeder_document_qs(request.user), pk=pk)

    if request.method == "POST":
        record.delete()
        messages.success(request, "Pomyślnie usunięto dokument.")
        return redirect("dashboard_documents")

    return render(
        request,
        "dashboard_documents/dashboard_documents_confirm_delete.html",
        {
            "record": record,
        },
    )
