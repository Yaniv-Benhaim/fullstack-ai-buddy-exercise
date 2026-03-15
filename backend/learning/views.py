from django.utils import timezone
from rest_framework import generics
from .models import Module, UserProgress, Notification
from .serializers import (
    ModuleSerializer,
    UserProgressSerializer,
    UserProgressUpdateSerializer,
    NotificationSerializer,
)

# TODO (Step 1): Uncomment the import below after
# implementing the Celery task in tasks.py
# from .tasks import generate_ai_nudge


class ModuleListView(generics.ListAPIView):
    """List all available learning modules."""

    queryset = Module.objects.all()
    serializer_class = ModuleSerializer


class UserProgressListView(generics.ListAPIView):
    """List progress for the current user."""

    serializer_class = UserProgressSerializer

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user).select_related(
            "module"
        )


class UserProgressUpdateView(generics.UpdateAPIView):
    """Update a progress record (e.g. mark a module as completed)."""

    serializer_class = UserProgressUpdateSerializer

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()

        # Set completed_at timestamp when status changes to completed
        if instance.status == "completed" and instance.completed_at is None:
            instance.completed_at = timezone.now()
            instance.save(update_fields=["completed_at"])

        # TODO (Step 1): Uncomment the lines below once you have
        # implemented generate_ai_nudge in tasks.py
        # if instance.status == "completed":
        #     generate_ai_nudge.delay(
        #         user_id=instance.user.id,
        #         module_id=instance.module.id,
        #     )


class NotificationListView(generics.ListAPIView):
    """List notifications for the current user."""

    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


# TODO (Step 2): Add a real-time endpoint here (SSE or WebSocket)
# to push new notifications to the frontend as they are created.
# See INSTRUCTIONS.md Step 2 for details.
