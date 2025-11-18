from django.contrib import admin
from .models import Opportunity

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "customer",
        "owner",
        "status",
        "amount",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
        "owner",
    )

    search_fields = (
        "title",
        "customer__name",
        "owner__username",
    )

    ordering = ("-created_at",)
