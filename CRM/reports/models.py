from django.db import models
from django.contrib.auth.models import User


class SavedReport(models.Model):
    """Guarda reportes generados para consulta posterior"""
    REPORT_TYPE_CHOICES = [
        ('sales', 'Reporte de Ventas'),
        ('customers', 'Reporte de Clientes'),
        ('sellers', 'Reporte de Vendedores'),
        ('followups', 'Reporte de Seguimientos'),
        ('opportunities', 'Reporte de Oportunidades'),
        ('pipeline', 'Análisis de Pipeline'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Título")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, verbose_name="Tipo de Reporte")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Creado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    start_date = models.DateField(null=True, blank=True, verbose_name="Fecha Inicio")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha Fin")
    data = models.JSONField(verbose_name="Datos del Reporte")
    
    class Meta:
        verbose_name = "Reporte Guardado"
        verbose_name_plural = "Reportes Guardados"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%d/%m/%Y')}"
