# followups/models.py
from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer


class FollowUp(models.Model):

    FOLLOWUP_TYPES = [
        ("llamada", "Llamada telefónica"),
        ("correo", "Correo electrónico"),
        ("reunión", "Reunión"),
        ("recordatorio", "Recordatorio"),
        ("otro", "Otro"),
    ]

    followup_type = models.CharField(
        max_length=20,
        choices=FOLLOWUP_TYPES
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    next_contact_date = models.DateField(
        blank=True,
        null=True
    )

    # 🔗 Cliente relacionado (opcional)
    related_customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="followups",
        null=True,
        blank=True,
    )

    # 🔗 Oportunidad relacionada (opcional)
    related_opportunity = models.ForeignKey(
        "opportunities.Opportunity",           # ← REFERENCIA EN STRING
        on_delete=models.CASCADE,
        related_name="followups",
        null=True,
        blank=True,
    )

    # 🔗 Quién creó el seguimiento
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_followups",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        target = self.related_customer or self.related_opportunity or "Sin destino"
        return f"{self.get_followup_type_display()} → {target} ({self.created_at.date()})"
