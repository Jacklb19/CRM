from django.urls import path
from .views import (
    FollowUpListView,
    FollowUpCreateView,
    FollowUpUpdateView,
    FollowUpDeleteView,
)
from . import views

app_name = "followups"

urlpatterns = [
    # LISTADO
    path("", FollowUpListView.as_view(), name="list"),

    # CREAR
    path("create/", FollowUpCreateView.as_view(), name="create"),

    # EDITAR
    path("<int:pk>/edit/", FollowUpUpdateView.as_view(), name="edit"),

    # ELIMINAR
    path("<int:pk>/delete/", FollowUpDeleteView.as_view(), name="delete"),
]
