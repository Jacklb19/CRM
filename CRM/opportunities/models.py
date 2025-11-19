from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from customers.models import Customer


class Opportunity(models.Model):
    STATUS_CHOICES = [
        ('abierta', 'Abierta'),
        ('calificada', 'Calificada'),
        ('propuesta', 'Propuesta enviada'),
        ('negociacion', 'En negociación'),
        ('ganada', 'Ganada'),
        ('perdida', 'Perdida'),
    ]
    
    PRIORITY_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Título")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='opportunities', verbose_name="Cliente")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='opportunities', verbose_name="Asignado a")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='abierta', verbose_name="Estado")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='media', verbose_name="Prioridad")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto estimado")
    expected_close_date = models.DateField(verbose_name="Fecha estimada de cierre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Oportunidad"
        verbose_name_plural = "Oportunidades"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['expected_close_date']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.customer.name}"
    
    def is_overdue(self):
        """Verifica si la oportunidad está vencida"""
        return self.status != 'ganada' and self.status != 'perdida' and self.expected_close_date < timezone.now().date()
    
    def days_until_close(self):
        """Calcula días hasta el cierre"""
        delta = self.expected_close_date - timezone.now().date()
        return delta.days
    
    def is_due_soon(self):
        """Verifica si la oportunidad vence en menos de 7 días"""
        days = self.days_until_close()
        return 0 <= days < 7 and self.status not in ['ganada', 'perdida']
