from django.contrib.auth.models import User
from rest_framework.authentication import BaseAuthentication


class AutoAuthMiddleware:
    """
    Auto-authenticate every request as the first user in the database.
    This removes all auth friction for the exercise — no login required.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = User.objects.first()
        if user:
            request.user = user
        return self.get_response(request)


class AutoAuthDRF(BaseAuthentication):
    """DRF authentication class that returns the user set by AutoAuthMiddleware."""

    def authenticate(self, request):
        user = getattr(request._request, "user", None)
        if user and user.is_authenticated:
            return (user, None)
        return None
