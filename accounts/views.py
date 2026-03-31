from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import BreederRegistrationForm


@login_required
def home_view(request):
    return render(request, "home.html")


def register_view(request):
    if request.method == "POST":
        form = BreederRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = BreederRegistrationForm()
    return render(request, "register.html", {"form": form})
