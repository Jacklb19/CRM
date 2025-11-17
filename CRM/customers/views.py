from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Customer
from .mixins import VendedorRequiredMixin

class CustomerListView(VendedorRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        # Buscar por nombre, email o empresa
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(company__icontains=search)
            )
        return queryset

class CustomerDetailView(VendedorRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'

class CustomerCreateView(VendedorRequiredMixin, CreateView):
    model = Customer
    fields = ['name', 'email', 'phone', 'company', 'is_active']
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')

class CustomerUpdateView(VendedorRequiredMixin, UpdateView):
    model = Customer
    fields = ['name', 'email', 'phone', 'company', 'is_active']
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customer_list')

class CustomerDeleteView(VendedorRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customers/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')
