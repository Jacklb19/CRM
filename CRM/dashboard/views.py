from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    """Vista principal del dashboard"""
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard/dashboard.html', context)
