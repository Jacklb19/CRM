from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from .forms import RegistrationForm, LoginForm, ProfileUpdateForm, AdminRegistrationForm
from .models import Profile
from django.views.generic import RedirectView


class HomeView(RedirectView):
    permanent = False
    
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse_lazy('dashboard')
        return reverse_lazy('login')


class AdminRequiredMixin:
    """Mixin para verificar que el usuario es administrador"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.profile.role != 'administrador':
            raise PermissionDenied("No tienes permisos para acceder a esta sección")
        return super().dispatch(request, *args, **kwargs)


class AdminRegisterView(CreateView):
    """Registro especial para el primer administrador (URL secreta)"""
    form_class = AdminRegistrationForm
    template_name = 'users/admin_register.html'
    success_url = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        admin_exists = User.objects.filter(profile__role='administrador').exists()
        
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
        print(form.errors)  # si quieres ver en consola qué falla
        messages.error(self.request, 'Por favor corrige los errores en el formulario.')
        return super().form_invalid(form)

class RegisterView(CreateView):
    """Vista para crear nuevos usuarios (solo admins desde el panel)"""
    form_class = RegistrationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('user_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Solo administradores autenticados pueden crear usuarios
        if request.user.is_authenticated and request.user.profile.role == 'administrador':
            return super().dispatch(request, *args, **kwargs)
        
        # Si no está autenticado, redirige al login
        if not request.user.is_authenticated:
            messages.error(request, 'Debes estar autenticado como administrador.')
            return redirect('login')
        
        # Si está autenticado pero no es admin, muestra error
        raise PermissionDenied("No tienes permisos para crear usuarios")
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance
        messages.success(self.request, f'Usuario {user.username} creado exitosamente.')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrige los errores en el formulario.')
        return super().form_invalid(form)


class UserListView(AdminRequiredMixin, ListView):
    """Panel de gestión de usuarios - solo administradores"""
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 10
    
    def get_queryset(self):
        return User.objects.filter(profile__isnull=False).select_related('profile')


class UserDetailView(AdminRequiredMixin, UpdateView):
    """Ver y editar detalles del usuario - solo administradores"""
    model = Profile
    fields = ['role', 'phone']
    template_name = 'users/user_detail.html'
    success_url = reverse_lazy('user_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.object.user
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Perfil de {self.object.user.username} actualizado.')
        return super().form_valid(form)


class UserDeleteView(AdminRequiredMixin, DeleteView):
    """Eliminar usuario - solo administradores"""
    model = User
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, f'Usuario {self.get_object().username} eliminado.')
        return super().delete(request, *args, **kwargs)


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


class UserLogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy('login')
    
    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'Has cerrado sesión exitosamente.')
        return super().dispatch(request, *args, **kwargs)


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
        context['user'] = self.request.user
        return context
