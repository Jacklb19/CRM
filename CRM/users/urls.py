from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home
    path('', views.HomeView.as_view(), name='home'),
    
    # URL secreta para crear el primer administrador
    path('admin-register/secret-key-12345/', views.AdminRegisterView.as_view(), name='admin_register'),
    
    # Gestión de usuarios (solo administrador)
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.RegisterView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', views.UserDetailView.as_view(), name='user_edit'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    # ⭐ Equipo de Ventas (NUEVO)
    path('team/', views.SalesTeamView.as_view(), name='sales_team'),
    
    # Autenticación
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Password reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='users/password_reset.html',
             email_template_name='users/password_reset_email.html',
             subject_template_name='users/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ),
         name='password_reset'),
    
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ),
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url='/password-reset-complete/'
         ),
         name='password_reset_confirm'),
    
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Password change
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='users/password_change.html',
             success_url='/profile/'
         ),
         name='password_change'),

    path('password-change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'
         ),
         name='password_change_done'),
]
