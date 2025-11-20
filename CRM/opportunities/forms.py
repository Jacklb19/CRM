from django import forms
from .models import Opportunity
from customers.models import Customer


class OpportunityForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # Recibir usuario desde la vista
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Estilos Bootstrap
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

        # Limitar probabilidad (input type number)
        self.fields["probability"].widget = forms.NumberInput(
            attrs={"min": 0, "max": 100, "class": "form-control"}
        )

        # Filtrar clientes si en el futuro quieres segmentar por vendedor
        # Por ahora mostramos todos, pero ya está preparado
        self.fields["customer"].queryset = Customer.objects.all()

    class Meta:
        model = Opportunity
        fields = [
            "title",
            "customer",
            "amount",
            "expected_close_date",
            "probability",
            "status",
            "description",
        ]
        widgets = {
            "expected_close_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }
