from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

from .models import Followup
from customers.models import Customer


# ============================================================
# FORMULARIO PRINCIPAL DE FOLLOWUPS (ACEPTANDO USER)
# ============================================================

class FollowupForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # Recibimos el user que la vista envía en get_form_kwargs
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filtrar clientes si el usuario es vendedor
        if self.user and self.user.profile.role == "vendedor":
            self.fields["customer"].queryset = Customer.objects.filter(
                assigned_to=self.user
            )
        # Admin / gerente ve todos
        else:
            self.fields["customer"].queryset = Customer.objects.all()

    class Meta:
        model = Followup
        fields = ['customer', 'type', 'subject', 'notes', 'date', 'status']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Asunto del seguimiento'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notas...'
            }),
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    # ------------------------
    # VALIDACIONES
    # ------------------------

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '').strip()

        if not subject:
            raise ValidationError("El asunto es obligatorio.")

        if len(subject) < 5:
            raise ValidationError("El asunto debe tener al menos 5 caracteres.")

        if len(subject) > 100:
            raise ValidationError("El asunto no puede exceder 100 caracteres.")

        return subject

    def clean_notes(self):
        notes = self.cleaned_data.get('notes', '').strip()

        if not notes:
            raise ValidationError("Las notas son obligatorias.")

        if len(notes) < 10:
            raise ValidationError("Las notas deben tener al menos 10 caracteres.")

        if len(notes) > 1000:
            raise ValidationError("Las notas no pueden exceder 1000 caracteres.")

        return notes

    def clean_date(self):
        date = self.cleaned_data.get('date')

        if not date:
            raise ValidationError("La fecha es obligatoria.")

        if date > timezone.now() + timezone.timedelta(days=365):
            raise ValidationError("La fecha no puede ser más de 1 año en el futuro.")

        return date

    def clean(self):
        cleaned_data = super().clean()
        customer = cleaned_data.get('customer')
        followup_type = cleaned_data.get('type')
        status = cleaned_data.get('status')
        date = cleaned_data.get('date')

        # Cliente activo
        if customer and not customer.is_active:
            raise ValidationError(
                f"El cliente '{customer.name}' está inactivo. Actívalo o elige otro cliente."
            )

        # Validación por tipo
        if followup_type == 'reunion' and status == 'completado':
            if date and date > timezone.now():
                raise ValidationError(
                    "No puedes marcar como completada una reunión futura."
                )

        return cleaned_data


# ============================================================
# FORMULARIO AVANZADO DE BÚSQUEDA
# ============================================================

class AdvancedFollowupSearchForm(forms.Form):
    """Formulario avanzado de búsqueda de seguimientos"""

    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por asunto, cliente, nota...',
        }),
        label='Búsqueda'
    )

    type = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('llamada', 'Llamada'),
            ('email', 'Email'),
            ('reunion', 'Reunión'),
            ('nota', 'Nota'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Tipos'
    )

    status = forms.MultipleChoiceField(
        required=False,
        choices=[
            ('pendiente', 'Pendiente'),
            ('completado', 'Completado'),
            ('vencido', 'Vencido'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Estados'
    )

    customer = forms.ModelChoiceField(
        required=False,
        queryset=Customer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Cliente',
        empty_label='Todos los clientes'
    )

    assigned_to = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(profile__role='vendedor'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Usuario',
        empty_label='Todos los usuarios'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha desde'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha hasta'
    )

    order_by = forms.ChoiceField(
        required=False,
        choices=[
            ('-date', 'Más recientes'),
            ('date', 'Más antiguos'),
            ('-created_at', 'Creados recientemente'),
            ('created_at', 'Creados antiguamente'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Ordenar por'
    )
