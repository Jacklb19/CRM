from django import forms
from .models import FollowUp
from customers.models import Customer
from opportunities.models import Opportunity

class FollowUpForm(forms.ModelForm):

    class Meta:
        model = FollowUp
        fields = [
            "followup_type",
            "notes",
            "next_contact_date",
            "related_customer",
            "related_opportunity",
        ]

        widgets = {
            "followup_type": forms.Select(attrs={
                "class": "form-select",
            }),

            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Escribe los detalles de la llamada, correo o reunión..."
            }),

            "next_contact_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control"
            }),

            "related_customer": forms.Select(attrs={
                "class": "form-select"
            }),

            "related_opportunity": forms.Select(attrs={
                "class": "form-select"
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  
        super().__init__(*args, **kwargs)

        # 🎯 Filtro inteligente según rol del usuario
        if user:

            role = user.profile.role

            # ADMIN → todo
            if role == "admin":
                self.fields["related_customer"].queryset = Customer.objects.all()
                self.fields["related_opportunity"].queryset = Opportunity.objects.all()

            # VENDEDOR → solo sus clientes y oportunidades
            elif role == "vendedor":
                self.fields["related_customer"].queryset = Customer.objects.filter(owner=user)
                self.fields["related_opportunity"].queryset = Opportunity.objects.filter(owner=user)

            # CLIENTE → no puede crear seguimientos
            else:
                self.fields["related_customer"].queryset = Customer.objects.none()
                self.fields["related_opportunity"].queryset = Opportunity.objects.none()

        # 🎨 Mejores opciones para followup_type
        self.fields["followup_type"].choices = [
            ("llamada", "📞 Llamada telefónica"),
            ("correo", "✉️ Correo electrónico"),
            ("reunión", "📅 Reunión"),
            ("recordatorio", "⏰ Recordatorio"),
            ("otro", "📝 Otro"),
        ]
