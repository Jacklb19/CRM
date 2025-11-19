from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer
from opportunities.models import Opportunity

class Followup(models.Model):
    TYPE_CHOICES = [
        ('llamada', 'Llamada'),
        ('email', 'Email'),
        ('reunion', 'Reunión'),
        ('nota', 'Nota'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='followups', verbose_name="Cliente")
    opportunity = models.ForeignKey(Opportunity, on_delete=models.SET_NULL, null=True, blank=True, related_name='followups', verbose_name="Oportunidad")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followups', verbose_name="Usuario")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='nota', verbose_name="Tipo")
    subject = models.CharField(max_length=200, verbose_name="Asunto")
    notes = models.TextField(verbose_name="Notas")
    date = models.DateTimeField(verbose_name="Fecha")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Seguimiento"
        verbose_name_plural = "Seguimientos"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.type} - {self.customer.name} - {self.date.strftime('%d/%m/%Y')}"
