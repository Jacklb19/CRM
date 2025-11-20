from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import models
from django.db.models import Q, Count
from .models import Customer
from .forms import AdvancedCustomerSearchForm
from .mixins import VendedorRequiredMixin


class CustomerListView(VendedorRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filtrado por rol
        if user.profile.role == 'vendedor':
            queryset = queryset.filter(assigned_to=user)
        
        # BÚSQUEDA AVANZADA
        form = AdvancedCustomerSearchForm(self.request.GET or None)
        
        search_query = self.request.GET.get('search_query', '').strip()
        search_by = self.request.GET.get('search_by', '')
        status = self.request.GET.get('status', '')
        assigned_to = self.request.GET.get('assigned_to', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        # Búsqueda por tipo específico
        if search_query:
            if search_by == 'name':
                queryset = queryset.filter(name__icontains=search_query)
            elif search_by == 'email':
                queryset = queryset.filter(email__icontains=search_query)
            elif search_by == 'id':
                try:
                    customer_id = int(search_query)
                    queryset = queryset.filter(id=customer_id)
                except ValueError:
                    queryset = queryset.none()
            elif search_by == 'company':
                queryset = queryset.filter(company__icontains=search_query)
            else:
                # Búsqueda global en todos los campos
                queryset = queryset.filter(
                    Q(name__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(company__icontains=search_query) |
                    Q(id__icontains=search_query)
                )
        
        # Filtro de estado
        if status == 'True':
            queryset = queryset.filter(is_active=True)
        elif status == 'False':
            queryset = queryset.filter(is_active=False)
        
        # Filtro de vendedor
        if assigned_to and user.profile.role != 'vendedor':
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        # Filtro de fecha
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Ordenamiento
        order_by = self.request.GET.get('order_by', '-created_at')
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AdvancedCustomerSearchForm(self.request.GET or None)
        
        # Estadísticas
        user = self.request.user
        if user.profile.role == 'vendedor':
            user_customers = Customer.objects.filter(assigned_to=user)
        else:
            user_customers = Customer.objects.all()
        
        context['total_customers'] = user_customers.count()
        context['active_customers'] = user_customers.filter(is_active=True).count()
        context['inactive_customers'] = user_customers.filter(is_active=False).count()
        
        return context


class CustomerDetailView(VendedorRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'


class CustomerCreateView(VendedorRequiredMixin, CreateView):
    model = Customer
    fields = ['name', 'email', 'phone', 'company', 'is_active']
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')
    
    def form_valid(self, form):
        if self.request.user.profile.role == 'vendedor':
            form.instance.assigned_to = self.request.user
        return super().form_valid(form)


class CustomerUpdateView(VendedorRequiredMixin, UpdateView):
    model = Customer
    fields = ['name', 'email', 'phone', 'company', 'is_active']
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.profile.role == 'vendedor':
            queryset = queryset.filter(assigned_to=user)
        return queryset


class CustomerDeleteView(VendedorRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.profile.role == 'vendedor':
            queryset = queryset.filter(assigned_to=user)
        return queryset
