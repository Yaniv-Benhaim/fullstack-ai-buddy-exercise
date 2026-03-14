from django.contrib.auth.models import User


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
