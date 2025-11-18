# opportunities/models.py
from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer


class Opportunity(models.Model):
    STATUS_CHOICES = [
        ("open", "Abierta"),
        ("won", "Ganada"),
        ("lost", "Perdida"),
    ]

    title = models.CharField(max_length=255)

    # Cliente asociado a la oportunidad
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="opportunities",
    )

    # Vendedor/propietario de la oportunidad
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opportunities",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="open",
    )

    probability = models.PositiveIntegerField(
        default=0,
        help_text="Probabilidad de cierre (0–100%)"
    )

    expected_close_date = models.DateField(
        null=True,
        blank=True,
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.customer})"
