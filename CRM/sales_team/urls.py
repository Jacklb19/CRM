from django.urls import path
from . import views

urlpatterns = [
    path('', views.SalesTeamListView.as_view(), name='sales_team_list'),
    path('<int:pk>/', views.SalesTeamDetailView.as_view(), name='sales_team_detail'),
]
