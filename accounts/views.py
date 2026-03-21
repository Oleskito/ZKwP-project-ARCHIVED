from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import BreederCreationForm


@login_required
def home_view(request):
    return render(request, "home.html")


def register_view(request):
    if request.method == "POST":
        form = BreederCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = BreederCreationForm()
    return render(request, "register.html", {"form": form})
