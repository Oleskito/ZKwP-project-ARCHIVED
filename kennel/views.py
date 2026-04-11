from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from .models import Dog, Litter, Puppy
from django.db.models import Q
from .forms import DogForm, LitterForm
from django.contrib import messages

@login_required
def dashboard_view(request):
    breeder = request.user
    active_dogs_count = Dog.objects.filter(breeder=breeder, breeding_status=Dog.BreedingStatus.ACTIVE).count()

    available_puppies_count = Puppy.objects.filter(breeder=breeder, status=Puppy.Status.AVAILABLE).count()

    active_litters_count = Litter.objects.filter(breeder=breeder, status__in=[Litter.Status.BORN, Litter.Status.REPORTED, Litter.Status.INSPECTED]).count()

    expected_litters_count = Litter.objects.filter(breeder=breeder, status__in=[Litter.Status.PLANNED, Litter.Status.MATED]).count()

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

    # --- 1. PARAMETRY ---
    q = request.GET.get('q', '').strip()
    selected_genders = request.GET.getlist('gender')
    selected_breeds = request.GET.getlist('breed')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    selected_statuses = request.GET.getlist('status')
    sort_by = request.GET.get('sort', 'name_asc')
    active_tab = request.GET.get('tab', 'active')  # 'active' lub 'archived'

    # --- 2. FILTRY GLOBALNE (Dla obu list i liczników) ---
    base_query = Dog.objects.filter(breeder=breeder)

    # Dynamiczne rasy dla Twojej hodowli
    available_breeds = base_query.exclude(breed__isnull=True).values_list('breed__name', flat=True).distinct()

    if q:
        base_query = base_query.filter(
            Q(name__icontains=q) | Q(chip_number__icontains=q) |
            Q(tattoo_number__icontains=q) | Q(pkr_number__icontains=q)
        )
    if selected_genders:
        base_query = base_query.filter(gender__in=selected_genders)
    if selected_breeds:
        base_query = base_query.filter(breed__name__in=selected_breeds)
    if date_from:
        base_query = base_query.filter(birth_date__gte=date_from)
    if date_to:
        base_query = base_query.filter(birth_date__lte=date_to)

    # --- 3. PODZIAŁ I LICZNIKI (Niezależne od statusu) ---
    # To gwarantuje, że (4) przy zakładce nie zniknie, gdy wybierzesz status
    active_base = base_query.filter(is_archived=False)
    archived_base = base_query.filter(is_archived=True)

    active_count = active_base.count()
    archived_count = archived_base.count()

    # --- 4. FILTROWANIE PO STATUSIE (Tylko dla aktualnej zakładki) ---
    active_dogs = active_base
    archived_dogs = archived_base

    if selected_statuses:
        if active_tab == 'active':
            active_dogs = active_base.filter(breeding_status__in=selected_statuses)
        else:
            archived_dogs = archived_base.filter(breeding_status__in=selected_statuses)

    # --- 5. SORTOWANIE ---
    sort_mapping = {
        'name_asc': 'name',
        'name_desc': '-name',
        'date_desc': '-birth_date',
        'date_asc': 'birth_date',
    }
    sort_field = sort_mapping.get(sort_by, 'name')
    active_dogs = active_dogs.order_by(sort_field)
    archived_dogs = archived_dogs.order_by(sort_field)

    context = {
        'active_dogs': active_dogs,
        'archived_dogs': archived_dogs,
        'active_count': active_count,
        'archived_count': archived_count,
        'available_breeds': available_breeds,
        'current_q': q,
        'current_genders': selected_genders,
        'current_breeds': selected_breeds,
        'current_statuses': selected_statuses,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'current_sort': sort_by,
        'active_tab': active_tab,
    }
    return render(request, "dashboard_dog/dashboard_dog.html", context)


@login_required
def dog_add_view(request):
    # Wyciągamy przydomek bezpośrednio z Twojego modelu Breeder
    # Jeśli jest pusty, używamy domyślnego tekstu
    user_kennel = request.user.kennel_name or "NIEUSTAWIONY PRZYDOMEK"

    if request.method == 'POST':
        # KLUCZOWE: Tutaj też musisz podać 'user', żeby walidacja unikalności zadziałała!
        form = DogForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            dog = form.save(commit=False)
            dog.breeder = request.user  # To jest ten "ręczny" balans dla commit=False
            dog.save()
            # Upewnij się, że masz taką nazwę URL w urls.py
            messages.success(request, f"Pomyślnie dodano psa {dog.name}!")
            return redirect('dashboard_dog')
    else:
        # Pusty formularz dla żądania GET
        form = DogForm(user=request.user)

    return render(request, 'dashboard_dog/dashboard_dog_add.html', {
        'form': form,
        'user_kennel': user_kennel
    })


@login_required
def dog_delete_view(request, pk):
    # Pobieramy psa lub wyrzucamy 404, jeśli nie należy do tego hodowcy
    dog = get_object_or_404(Dog, pk=pk, breeder=request.user)

    if request.method == 'POST':
        dog.delete()  # To jest trwałe usunięcie z bazy (Hard Delete)
        messages.success(request, f"Pomyślnie usunięto psa {dog.name}!")
        return redirect('dashboard_dog')

    # Przekierowanie do strony z wielkim czerwonym ostrzeżeniem
    return render(request, 'dashboard_dog/dashboard_dog_confirm_delete.html', {'dog': dog})


@login_required
def dog_edit_view(request, pk):
    # Pobieramy konkretnego psa, pilnując, by należał do zalogowanego hodowcy
    dog = get_object_or_404(Dog, pk=pk, breeder=request.user)

    if request.method == 'POST':
        # Kluczowe: przekazujemy 'instance=dog', żeby Django wiedziało,
        # że edytujemy istniejący rekord, a nie tworzymy nowy.
        form = DogForm(request.POST, request.FILES, instance=dog, user=request.user)

        if form.is_valid():
            form.save()  # Metoda save() w modelu automatycznie zadba o is_archived
            messages.success(request, f"Pomyślnie zaktualizowano psa {dog.name}!")
            return redirect('dashboard_dog')
        else:
            print(form.errors)
    else:
        # GET: Formularz wypełniony danymi psa
        form = DogForm(instance=dog, user=request.user)

    return render(request, 'dashboard_dog/dashboard_dog_edit.html', {
        'form': form,
        'dog': dog
    })


@login_required
def dashboard_litter_view(request):
    breeder = request.user

    # --- PARAMETRY ---
    q = request.GET.get('q', '').strip()
    selected_statuses = request.GET.getlist('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    mating_date_from = request.GET.get('mating_date_from')
    mating_date_to = request.GET.get('mating_date_to')
    sort_by = request.GET.get('sort', 'date_desc')
    active_tab = request.GET.get('tab', 'active')

    base_query = Litter.objects.filter(breeder=breeder)

    if q:
        base_query = base_query.filter(litter_letter__icontains=q)
    if date_from:
        base_query = base_query.filter(birth_date__gte=date_from)
    if date_to:
        base_query = base_query.filter(birth_date__lte=date_to)
    if mating_date_from:
        base_query = base_query.filter(mating_date_start__gte=mating_date_from)
    if mating_date_to:
        base_query = base_query.filter(mating_date_start__lte=mating_date_to)

    # --- PODZIAŁ: Aktywne to wszystkie z wyjątkiem ARCHIVED ---
    active_base = base_query.exclude(status=Litter.Status.ARCHIVED)
    archived_base = base_query.filter(status=Litter.Status.ARCHIVED)

    active_count = active_base.count()
    archived_count = archived_base.count()

    active_litters = active_base
    archived_litters = archived_base

    if selected_statuses:
        if active_tab == 'active':
            active_litters = active_base.filter(status__in=selected_statuses)
        else:
            archived_litters = archived_base.filter(status__in=selected_statuses)

    # --- SORTOWANIE ---
    sort_mapping = {
        'date_desc': '-birth_date',
        'date_asc': 'birth_date',
        'letter_asc': 'litter_letter',
        'letter_desc': '-litter_letter',
    }
    # Używamy "-birth_date" jako domyślnego, bo najnowsze mioty są najważniejsze
    sort_field = sort_mapping.get(sort_by, '-birth_date')
    active_litters = active_litters.order_by(sort_field)
    archived_litters = archived_litters.order_by(sort_field)

    context = {
        'active_litters': active_litters,
        'archived_litters': archived_litters,
        'active_count': active_count,
        'archived_count': archived_count,
        'current_q': q,
        'current_statuses': selected_statuses,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'current_sort': sort_by,
        'active_tab': active_tab,
        'current_mating_date_from': mating_date_from,
        'current_mating_date_to': mating_date_to,
    }
    return render(request, "dashboard_litter/dashboard_litter.html", context)

@login_required
def litter_add_view(request):
    if request.method == 'POST':
        form = LitterForm(request.POST, user=request.user)
        if form.is_valid():
            litter = form.save(commit=False)
            litter.breeder = request.user
            litter.save()
            messages.success(request, f"Pomyślnie dodano miot {litter.litter_letter or ''}!")
            return redirect('dashboard_litter') # Upewnij się, że tak nazywa się Twój url dla listy miotów
    else:
        form = LitterForm(user=request.user)

    return render(request, 'dashboard_litter/dashboard_litter_add.html', {'form': form})


@login_required
def litter_edit_view(request, pk):
    # Pobieramy miot, upewniając się, że należy do zalogowanego hodowcy
    litter = get_object_or_404(Litter, pk=pk, breeder=request.user)

    if request.method == 'POST':
        # Przekazujemy instance=litter, by Django wiedziało, że edytujemy, a nie tworzymy nowy!
        form = LitterForm(request.POST, instance=litter, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, f"Pomyślnie zaktualizowano miot {litter.litter_letter or ''}!")
            return redirect('dashboard_litter')
    else:
        # GET: Wypełniamy formularz danymi z bazy
        form = LitterForm(instance=litter, user=request.user)

    return render(request, 'dashboard_litter/dashboard_litter_edit.html', {
        'form': form,
        'litter': litter
    })


@login_required
def litter_delete_view(request, pk):
    # Pobieramy miot i upewniamy się, że należy do aktualnie zalogowanego użytkownika
    litter = get_object_or_404(Litter, pk=pk, breeder=request.user)

    if request.method == 'POST':
        # Zapisujemy literę do komunikatu, zanim usuniemy obiekt
        letter = litter.litter_letter or "bez litery"
        litter.delete()
        messages.success(request, f"Pomyślnie usunięto miot {letter}.")
        return redirect('dashboard_litter')

    return render(request, 'dashboard_litter/dashboard_litter_confirm_delete.html', {'litter': litter})