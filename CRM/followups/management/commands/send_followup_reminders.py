from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from followups.models import Followup


class Command(BaseCommand):
    help = 'Envía recordatorios de seguimientos vencidos o próximos a vencer'

    def handle(self, *args, **options):
        if not getattr(settings, 'FOLLOWUP_REMINDER_ENABLED', True):
            self.stdout.write(self.style.WARNING('Recordatorios deshabilitados en settings'))
            return

        now = timezone.now()
        reminders_sent = 0
        
        # 1. Seguimientos vencidos (pasado su fecha programada)
        overdue_followups = Followup.objects.filter(
            status='pendiente',
            date__lt=now,
            is_reminder_sent=False
        )
        
        for followup in overdue_followups:
            self.send_reminder_email(followup, 'VENCIDO')
            followup.status = 'vencido'
            followup.is_reminder_sent = True
            followup.save()
            reminders_sent += 1
            self.stdout.write(
                self.style.SUCCESS(f'✓ Recordatorio vencido enviado: {followup.subject}')
            )
        
        # 2. Seguimientos próximos a vencer (próximas 24 horas)
        soon_followups = Followup.objects.filter(
            status='pendiente',
            date__gte=now,
            date__lte=now + timedelta(hours=24),
            is_reminder_sent=False
        )
        
        for followup in soon_followups:
            self.send_reminder_email(followup, 'PRÓXIMO A VENCER')
            followup.is_reminder_sent = True
            followup.save()
            reminders_sent += 1
            self.stdout.write(
                self.style.SUCCESS(f'✓ Recordatorio próximo enviado: {followup.subject}')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total de recordatorios enviados: {reminders_sent}')
        )

    def send_reminder_email(self, followup, status_type):
        """Envía un email de recordatorio"""
        
        subject = f"[CRM] Recordatorio: {status_type} - {followup.subject}"
        
        # Cuerpo del email
        message = f"""
Hola {followup.user.first_name or followup.user.username},

Tienes un seguimiento {status_type}:

═══════════════════════════════════════════════════════════

📋 DETALLES DEL SEGUIMIENTO
───────────────────────────────────────────────────────────
Asunto:           {followup.subject}
Cliente:          {followup.customer.name}
Tipo:             {followup.get_type_display()}
Fecha programada: {followup.date.strftime('%d/%m/%Y %H:%M')}
Estado:           {followup.get_status_display()}

"""
        
        if followup.opportunity:
            message += f"Oportunidad:      {followup.opportunity.title}\n"
        
        message += f"""
═══════════════════════════════════════════════════════════

💬 NOTAS
───────────────────────────────────────────────────────────
{followup.notes}

═══════════════════════════════════════════════════════════

Por favor, revisa y actualiza el estado en el CRM.

Saludos,
Sistema CRM Pro
"""
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@crm.local'),
                recipient_list=[followup.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Error enviando email a {followup.user.email}: {e}")
