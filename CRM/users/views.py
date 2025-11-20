from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DeleteView, RedirectView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.db.models import Q, Count, Sum
from .forms import RegistrationForm, LoginForm, ProfileUpdateForm, AdminRegistrationForm
from .models import Profile


# ================================================================
# HOME
# ================================================================

class HomeView(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse_lazy('dashboard')
        return reverse_lazy('login')


# ================================================================
# MIXIN PARA VERIFICAR ADMINISTRADOR
# ================================================================

class AdminRequiredMixin:
    """Mixin para verificar que el usuario es administrador"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.profile.role != 'administrador':
            raise PermissionDenied("No tienes permisos para acceder a esta sección")
        return super().dispatch(request, *args, **kwargs)


# ================================================================
# REGISTRO ESPECIAL DEL PRIMER ADMIN
# ================================================================

class AdminRegisterView(CreateView):
    form_class = AdminRegistrationForm
    template_name = 'users/admin_register.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        admin_exists = User.objects.filter(profile__role='administrador').exists()

        # Si ya hay admins, solo un admin existente puede crear más
        if admin_exists and not request.user.is_authenticated:
            messages.error(request, 'El registro de administradores está deshabilitado.')
            return redirect('login')

        if request.user.is_authenticated and request.user.profile.role != 'administrador':
            raise PermissionDenied("No tienes permisos para crear administradores")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        profile = user.profile
        profile.role = 'administrador'
        profile.save()

        messages.success(self.request, f'Administrador {user.username} creado exitosamente.')
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrige los errores en el formulario.')
        return super().form_invalid(form)


# ================================================================
# REGISTRO DE USUARIOS (ADMIN PANEL)
# ================================================================

class RegisterView(CreateView):
    form_class = RegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('user_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.role == 'administrador':
            return super().dispatch(request, *args, **kwargs)

        if not request.user.is_authenticated:
            messages.error(request, 'Debes estar autenticado como administrador.')
            return redirect('login')

        raise PermissionDenied("No tienes permisos para crear usuarios")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        messages.success(self.request, f'Usuario {user.username} creado exitosamente.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrige los errores en el formulario.')
        return super().form_invalid(form)


# ================================================================
# LISTA DE USUARIOS
# ================================================================

class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        # Obtener todos los usuarios con perfil
        queryset = User.objects.filter(
            profile__isnull=False
        ).select_related('profile').order_by('id')

        # Aplicar filtros de búsqueda
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        # Filtro por rol
        role_filter = self.request.GET.get('role', '')
        if role_filter:
            queryset = queryset.filter(profile__role=role_filter)

        return queryset

    def get_context_data(self, **kwargs):
        """Agregar estadísticas al contexto"""
        context = super().get_context_data(**kwargs)
        
        # Calcular estadísticas de TODOS los usuarios (sin filtros)
        all_users = User.objects.filter(profile__isnull=False).select_related('profile')
        
        context['total_admins'] = all_users.filter(profile__role='administrador').count()
        context['total_managers'] = all_users.filter(profile__role='gerente').count()
        context['total_salespeople'] = all_users.filter(profile__role='vendedor').count()
        
        return context


# ================================================================
# EQUIPO DE VENTAS ⭐ NUEVO ⭐
# ================================================================

class SalesTeamView(LoginRequiredMixin, ListView):
    """Vista para mostrar el equipo de ventas con sus estadísticas"""
    model = User
    template_name = 'users/sales_team.html'
    context_object_name = 'team_members'
    
    def get_queryset(self):
        # Solo mostrar vendedores y gerentes
        return User.objects.filter(
            profile__role__in=['vendedor', 'gerente']
        ).select_related('profile').annotate(
            # Contar clientes asignados
            total_customers=Count('customer', distinct=True),
            # Contar oportunidades asignadas
            total_opportunities=Count('opportunity', distinct=True),
            # Contar oportunidades ganadas
            won_opportunities=Count(
                'opportunity',
                filter=Q(opportunity__status='ganada'),
                distinct=True
            ),
            # Sumar pipeline activo (oportunidades abiertas)
            total_pipeline=Sum(
                'opportunity__amount',
                filter=Q(opportunity__status__in=['abierta', 'calificada', 'propuesta', 'negociacion'])
            )
        ).order_by('-total_pipeline')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales del equipo
        all_team = self.get_queryset()
        
        context['total_team_members'] = all_team.count()
        context['total_pipeline'] = all_team.aggregate(Sum('total_pipeline'))['total_pipeline__sum'] or 0
        context['total_won'] = all_team.aggregate(Sum('won_opportunities'))['won_opportunities__sum'] or 0
        context['total_opportunities'] = all_team.aggregate(Sum('total_opportunities'))['total_opportunities__sum'] or 0
        
        return context


# ================================================================
# DETALLE / EDICIÓN DE PERFIL DE USUARIO POR ADMIN
# ================================================================

class UserDetailView(AdminRequiredMixin, UpdateView):
    model = Profile
    fields = ['role', 'phone']
    template_name = 'users/user_detail.html'
    success_url = reverse_lazy('user_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.object.user  # evitar conflicto con request.user
        return context

    def form_valid(self, form):
        messages.success(self.request, f'Perfil de {self.object.user.username} actualizado.')
        return super().form_valid(form)


# ================================================================
# ELIMINACIÓN DE USUARIOS
# ================================================================

class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Usuario {self.get_object().username} eliminado.')
        return super().delete(request, *args, **kwargs)


# ================================================================
# LOGIN
# ================================================================

class UserLoginView(LoginView):
    form_class = LoginForm
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard')

    def form_valid(self, form):
        messages.success(self.request, f'¡Bienvenido de nuevo, {form.get_user().username}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Usuario o contraseña incorrectos.')
        return super().form_invalid(form)


# ================================================================
# LOGOUT
# ================================================================

class UserLogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Has cerrado sesión exitosamente.')
        return super().dispatch(request, *args, **kwargs)


# ================================================================
# PERFIL DEL USUARIO (AUTOGESTIÓN)
# ================================================================

class ProfileView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, 'Tu perfil ha sido actualizado correctamente.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_obj'] = self.request.user
        return context
