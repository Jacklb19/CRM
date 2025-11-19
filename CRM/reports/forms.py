from django import forms
from customers.models import Customer
from users.models import Profile
from customers.models import Customer
from django.contrib.auth.models import User

class ReportFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), required=False)
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(profile__role='vendedor'),
        required=False,
        label='Vendedor'
    )
    # Añade filtros para oportunidades, estados, etc según vayas implementando esas apps
    # Por ejemplo:
    # opportunity_status = forms.ChoiceField(choices=[('', 'Todos'), ('abierta', 'Abierta'), ('ganada', 'Ganada'), ('perdida', 'Perdida')], required=False)
