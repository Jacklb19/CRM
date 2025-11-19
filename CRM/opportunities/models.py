from django.db import models
from django.contrib.auth.models import User
from customers.models import Customer

class Opportunity(models.Model):
    STATUS_CHOICES = [
        ('abierta', 'Abierta'),
        ('ganada', 'Ganada'),
        ('perdida', 'Perdida'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Título")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='opportunities', verbose_name="Cliente")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='opportunities', verbose_name="Asignado a")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='abierta', verbose_name="Estado")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto estimado")
    expected_close_date = models.DateField(verbose_name="Fecha estimada de cierre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Oportunidad"
        verbose_name_plural = "Oportunidades"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.customer.name}"
