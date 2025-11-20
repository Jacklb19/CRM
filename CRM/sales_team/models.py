from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class TeamMember(models.Model):
    """Extensión del User con información de equipo de ventas"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='team_member')
    department = models.CharField(max_length=100, blank=True, verbose_name="Departamento")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    hire_date = models.DateField(null=True, blank=True, verbose_name="Fecha de contratación")
    is_active_seller = models.BooleanField(default=True, verbose_name="Vendedor activo")
    
    class Meta:
        verbose_name = "Miembro del equipo"
        verbose_name_plural = "Miembros del equipo"
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"
    
    def get_total_opportunities(self):
        """Total de oportunidades asignadas"""
        return self.user.opportunities.count()
    
    def get_open_opportunities(self):
        """Oportunidades abiertas"""
        return self.user.opportunities.filter(
            status__in=['abierta', 'calificada', 'propuesta', 'negociacion']
        ).count()
    
    def get_won_opportunities(self):
        """Oportunidades ganadas"""
        return self.user.opportunities.filter(status='ganada').count()
    
    def get_lost_opportunities(self):
        """Oportunidades perdidas"""
        return self.user.opportunities.filter(status='perdida').count()
    
    def get_total_pipeline_value(self):
        """Valor total en pipeline (abiertas)"""
        from opportunities.models import Opportunity
        opps = Opportunity.objects.filter(
            assigned_to=self.user,
            status__in=['abierta', 'calificada', 'propuesta', 'negociacion']
        )
        return sum(opp.amount for opp in opps)
    
    def get_won_value(self):
        """Valor total ganado"""
        from opportunities.models import Opportunity
        opps = Opportunity.objects.filter(
            assigned_to=self.user,
            status='ganada'
        )
        return sum(opp.amount for opp in opps)
    
    def get_average_deal_size(self):
        """Tamaño promedio de trato"""
        from opportunities.models import Opportunity
        opps = Opportunity.objects.filter(assigned_to=self.user)
        if opps.count() == 0:
            return 0
        return sum(opp.amount for opp in opps) / opps.count()
    
    def get_win_rate(self):
        """Tasa de cierre"""
        total = self.get_total_opportunities()
        if total == 0:
            return 0
        won = self.get_won_opportunities()
        return round((won / total) * 100, 2)
    
    def get_followups_count(self):
        """Total de seguimientos realizados"""
        return self.user.followups.count()
    
    def get_total_customers(self):
        """Total de clientes asignados"""
        return self.user.customers.count()


# ============= SIGNALS =============

@receiver(post_save, sender=User)
def create_team_member_for_seller(sender, instance, created, **kwargs):
    """
    Crear automáticamente TeamMember cuando se crea un usuario
    con rol de vendedor o gerente
    """
    # Solo proceder si el usuario tiene perfil
    if not hasattr(instance, 'profile'):
        return
    
    role = instance.profile.role
    
    # Si es vendedor o gerente, crear TeamMember si no existe
    if role in ['vendedor', 'gerente']:
        TeamMember.objects.get_or_create(
            user=instance,
            defaults={
                'is_active_seller': True,
                'hire_date': timezone.now().date()
            }
        )


@receiver(post_save, sender=User)
def update_team_member_status(sender, instance, created, **kwargs):
    """
    Actualizar is_active_seller si el usuario cambia de rol
    """
    if created:
        return  # Ya lo maneja create_team_member_for_seller
    
    if not hasattr(instance, 'profile'):
        return
    
    role = instance.profile.role
    
    # Si tiene TeamMember, actualizar su estado según el rol
    if hasattr(instance, 'team_member'):
        if role in ['vendedor', 'gerente']:
            instance.team_member.is_active_seller = True
            instance.team_member.save()
        else:
            # Si cambió a administrador, desactivar como vendedor
            instance.team_member.is_active_seller = False
            instance.team_member.save()
