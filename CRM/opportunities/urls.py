from django.urls import path
from . import views

urlpatterns = [
    path('', views.OpportunityListView.as_view(), name='opportunity_list'),
    path('<int:pk>/', views.OpportunityDetailView.as_view(), name='opportunity_detail'),
    path('create/', views.OpportunityCreateView.as_view(), name='opportunity_create'),
    path('<int:pk>/update/', views.OpportunityUpdateView.as_view(), name='opportunity_update'),
    path('<int:pk>/delete/', views.OpportunityDeleteView.as_view(), name='opportunity_delete'),
]
