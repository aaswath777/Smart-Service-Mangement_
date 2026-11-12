from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User


def get_effective_role(user):
    """Superusers are always treated as administrators."""
    if user.is_superuser or user.is_platform_admin:
        return User.Role.ADMIN
    return user.role


def role_required(*allowed_roles):
    """
    Protect a view:
      - not logged in  -> redirected to the login page
      - wrong role     -> 403 Access denied page
    """

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if get_effective_role(request.user) not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator