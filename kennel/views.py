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
