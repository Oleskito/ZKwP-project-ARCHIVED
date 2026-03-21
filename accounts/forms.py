from django.contrib.auth.forms import UserCreationForm

from .models import Breeder


class BreederCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Breeder
        fields = ("email", "first_name", "last_name")
