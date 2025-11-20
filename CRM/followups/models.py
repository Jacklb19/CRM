from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from customers.models import Customer
from opportunities.models import Opportunity


class Followup(models.Model):
    TYPE_CHOICES = [
        ('llamada', 'Llamada'),
        ('email', 'Email'),
        ('reunion', 'Reunión'),
        ('nota', 'Nota'),
    ]
    
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('vencido', 'Vencido'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='followups', verbose_name="Cliente")
    opportunity = models.ForeignKey(Opportunity, on_delete=models.SET_NULL, null=True, blank=True, related_name='followups', verbose_name="Oportunidad")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followups', verbose_name="Usuario responsable")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='nota', verbose_name="Tipo")
    subject = models.CharField(max_length=200, verbose_name="Asunto")
    notes = models.TextField(verbose_name="Notas")
    date = models.DateTimeField(verbose_name="Fecha programada")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente', verbose_name="Estado")
    is_reminder_sent = models.BooleanField(default=False, verbose_name="Recordatorio enviado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Seguimiento"
        verbose_name_plural = "Seguimientos"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.type} - {self.customer.name} - {self.date.strftime('%d/%m/%Y %H:%M')}"
    
    def is_overdue(self):
        """Verifica si el seguimiento está vencido"""
        return self.status == 'pendiente' and self.date < timezone.now()
    
    def is_due_soon(self):
        """Verifica si el seguimiento vence en menos de 24 horas"""
        now = timezone.now()
        time_until = self.date - now
        return self.status == 'pendiente' and time_until.total_seconds() < 86400 and time_until.total_seconds() > 0
