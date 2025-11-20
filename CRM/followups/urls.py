from django.urls import path
from . import views

urlpatterns = [
    path('', views.FollowupListView.as_view(), name='followup_list'),
    path('<int:pk>/', views.FollowupDetailView.as_view(), name='followup_detail'),
    path('create/', views.FollowupCreateView.as_view(), name='followup_create'),
    path('<int:pk>/update/', views.FollowupUpdateView.as_view(), name='followup_update'),
    path('<int:pk>/delete/', views.FollowupDeleteView.as_view(), name='followup_delete'),
]
