from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import Dog, Litter, Puppy

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
    return render(request, "dashboard.html", context)

@login_required
def dashboard_dog_view(request):
    breeder = request.user

    # 1. Moje stado (Psy aktywne i w przygotowaniu, nie zarchiwizowane)
    active_dogs = Dog.objects.filter(
        breeder=breeder,
        is_archived=False,
        breeding_status__in=[
            Dog.BreedingStatus.ACTIVE,
            Dog.BreedingStatus.IN_PREPARATION
        ]
    ).order_by('name')

    # 2. Archiwum (Zarchiwizowane)
    archived_dogs = Dog.objects.filter(
        breeder=breeder,
        is_archived=True
    ).order_by('name')

    context = {
        'active_dogs': active_dogs,
        'archived_dogs': archived_dogs,
    }

    return render(request, "dashboard_dog.html", context)