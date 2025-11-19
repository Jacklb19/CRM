from django import forms
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .models import Opportunity
from .forms import OpportunityForm
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User

class VendedorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        
        role = getattr(request.user.profile, 'role', None)
        if role not in ['vendedor', 'gerente', 'administrador']:
            raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)

class OpportunityListView(VendedorRequiredMixin, ListView):
    model = Opportunity
    template_name = 'opportunities/opportunity_list.html'
    context_object_name = 'opportunities'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        vendedores = User.objects.filter(profile__role='vendedor')
        queryset = queryset.filter(assigned_to__in=vendedores)
        # Vendedores solo ven sus oportunidades
        if self.request.user.profile.role == 'vendedor':
            queryset = queryset.filter(assigned_to=self.request.user)
        
        # Filtros opcionales
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        return queryset

class OpportunityDetailView(VendedorRequiredMixin, DetailView):
    model = Opportunity
    template_name = 'opportunities/opportunity_detail.html'

class OpportunityCreateView(VendedorRequiredMixin, CreateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/opportunity_form.html'
    success_url = reverse_lazy('opportunity_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.profile.role == 'vendedor':
            form.fields['assigned_to'].widget = forms.HiddenInput()
        return form

    def form_valid(self, form):
        if self.request.user.profile.role == 'vendedor':
            form.instance.assigned_to = self.request.user
        return super().form_valid(form)

class OpportunityUpdateView(VendedorRequiredMixin, UpdateView):
    model = Opportunity
    form_class = OpportunityForm
    template_name = 'opportunities/opportunity_form.html'
    success_url = reverse_lazy('opportunity_list')
    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if self.request.user.profile.role == 'vendedor':
            form.fields['assigned_to'].widget = forms.HiddenInput()
        return form


class OpportunityDeleteView(VendedorRequiredMixin, DeleteView):
    model = Opportunity
    template_name = 'opportunities/opportunity_confirm_delete.html'
    success_url = reverse_lazy('opportunity_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.profile.role == 'vendedor' and obj.assigned_to != request.user:
            raise PermissionDenied("No tienes permiso para eliminar esta oportunidad.")
        return super().dispatch(request, *args, **kwargs)
