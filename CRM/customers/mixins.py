from django.core.exceptions import PermissionDenied

class VendedorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or getattr(request.user.profile, 'role', None) != 'vendedor':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
