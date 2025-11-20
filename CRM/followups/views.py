import logging
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages

from .models import Followup
from .forms import FollowupForm, AdvancedFollowupSearchForm


logger = logging.getLogger(__name__)


# ===============================================================
# MIXIN DE PERMISOS
# ===============================================================

class VendedorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        
        role = getattr(request.user.profile, 'role', None)
        if role not in ['vendedor', 'gerente', 'administrador']:
            raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)


# ===============================================================
# LISTA DE SEGUIMIENTOS (BÚSQUEDA AVANZADA)
# ===============================================================

class FollowupListView(VendedorRequiredMixin, ListView):
    model = Followup
    template_name = 'followups/followup_list.html'
    context_object_name = 'followups'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Filtrar según rol
        if user.profile.role == 'vendedor':
            queryset = queryset.filter(user=user)

        # --------------------------
        # FILTROS AVANZADOS
        # --------------------------
        search_query = self.request.GET.get('search_query', '').strip()
        type_filter = self.request.GET.getlist('type')
        status_filter = self.request.GET.getlist('status')
        customer_filter = self.request.GET.get('customer', '')
        assigned_to_filter = self.request.GET.get('assigned_to', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        order_by = self.request.GET.get('order_by', '-date')

        # Texto libre
        if search_query:
            queryset = queryset.filter(
                Q(subject__icontains=search_query) |
                Q(notes__icontains=search_query) |
                Q(customer__name__icontains=search_query)
            )

        # Tipo
        if type_filter:
            queryset = queryset.filter(type__in=type_filter)

        # Estado
        if status_filter:
            queryset = queryset.filter(status__in=status_filter)

        # Cliente
        if customer_filter:
            queryset = queryset.filter(customer_id=customer_filter)

        # Usuario asignado (solo gerentes/admins)
        if assigned_to_filter and user.profile.role != 'vendedor':
            queryset = queryset.filter(user_id=assigned_to_filter)

        # Fechas
        if date_from:
            queryset = queryset.filter(date__gte=date_from)

        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        # Ordenar
        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset.select_related('customer', 'user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['form'] = AdvancedFollowupSearchForm(self.request.GET or None)

        # Estadísticas
        if user.profile.role == 'vendedor':
            followups = Followup.objects.filter(user=user)
        else:
            followups = Followup.objects.all()

        context['total_followups'] = followups.count()
        context['pending_followups'] = followups.filter(status='pendiente').count()
        context['completed_followups'] = followups.filter(status='completado').count()

        return context


# ===============================================================
# DETALLE ⭐ CORREGIDO ⭐
# ===============================================================

class FollowupDetailView(VendedorRequiredMixin, DetailView):
    model = Followup
    template_name = 'followups/followup_detail.html'
    context_object_name = 'followup'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if request.user.profile.role == 'vendedor' and obj.user != request.user:
            raise PermissionDenied("No tienes permiso para ver este seguimiento.")

        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """⭐ Procesar datos que necesiten división ⭐"""
        context = super().get_context_data(**kwargs)
        followup = self.object
        
        # Si tienes un campo 'notes' que tiene múltiples líneas
        # Dividirlo por saltos de línea para mostrarlo mejor
        if followup.notes:
            context['notes_lines'] = followup.notes.split('\n')
        else:
            context['notes_lines'] = []
        
        # Si tienes tags separados por comas
        # context['tags_list'] = followup.tags.split(',') if hasattr(followup, 'tags') and followup.tags else []
        
        # Si tienes participantes separados por algún delimitador
        # context['participants_list'] = followup.participants.split(';') if hasattr(followup, 'participants') and followup.participants else []
        
        return context


# ===============================================================
# CREAR SEGUIMIENTO
# ===============================================================

class FollowupCreateView(VendedorRequiredMixin, CreateView):
    model = Followup
    form_class = FollowupForm
    template_name = 'followups/followup_form.html'
    success_url = reverse_lazy('followup_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = 'pendiente'
        
        messages.success(
            self.request, 
            f'Seguimiento "{form.instance.subject}" creado exitosamente.'
        )
        
        logger.info(f"Nuevo seguimiento creado por {self.request.user}: {form.instance.subject}")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Por favor corrige los errores en el formulario.'
        )
        logger.warning(f"Formulario inválido para usuario {self.request.user}: {form.errors}")
        return super().form_invalid(form)


# ===============================================================
# ACTUALIZAR SEGUIMIENTO
# ===============================================================

class FollowupUpdateView(VendedorRequiredMixin, UpdateView):
    model = Followup
    form_class = FollowupForm
    template_name = 'followups/followup_form.html'
    success_url = reverse_lazy('followup_list')
    context_object_name = 'followup'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if request.user.profile.role == 'vendedor' and obj.user != request.user:
            raise PermissionDenied("No tienes permiso para editar este seguimiento.")

        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(
            self.request,
            f'Seguimiento "{form.instance.subject}" actualizado exitosamente.'
        )
        logger.info(f"Seguimiento actualizado por {self.request.user}: {form.instance.subject}")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'Por favor corrige los errores en el formulario.'
        )
        logger.warning(f"Formulario inválido para usuario {self.request.user}: {form.errors}")
        return super().form_invalid(form)


# ===============================================================
# ELIMINAR SEGUIMIENTO
# ===============================================================

class FollowupDeleteView(VendedorRequiredMixin, DeleteView):
    model = Followup
    template_name = 'followups/followup_confirm_delete.html'
    success_url = reverse_lazy('followup_list')
    context_object_name = 'followup'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()

        if request.user.profile.role == 'vendedor' and obj.user != request.user:
            raise PermissionDenied("No tienes permiso para eliminar este seguimiento.")

        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        followup = self.get_object()
        messages.success(
            request,
            f'Seguimiento "{followup.subject}" eliminado exitosamente.'
        )
        logger.info(f"Seguimiento eliminado por {request.user}: {followup.subject}")
        return super().delete(request, *args, **kwargs)
