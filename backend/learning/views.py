import json

from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import generics
from .models import Module, UserProgress, Notification
from .serializers import (
    ModuleSerializer,
    UserProgressSerializer,
    UserProgressUpdateSerializer,
    NotificationSerializer,
)
from .tasks import generate_ai_nudge


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
        previous_status = serializer.instance.status
        instance = serializer.save()
        became_completed = (
            previous_status != UserProgress.Status.COMPLETED
            and instance.status == UserProgress.Status.COMPLETED
        )

        # Set completed_at timestamp when status changes to completed
        if became_completed and instance.completed_at is None:
            instance.completed_at = timezone.now()
            instance.save(update_fields=["completed_at"])

        if became_completed:
            generate_ai_nudge.delay(
                user_id=instance.user.id,
                module_id=instance.module.id,
            )


class NotificationListView(generics.ListAPIView):
    """List notifications for the current user."""

    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class NotificationStreamView(generics.GenericAPIView):
    """Stream live notifications for the current user with Server-Sent Events."""

    def get(self, request, *args, **kwargs):
        from .tasks import get_redis_client, notification_channel

        channel = notification_channel(request.user.id)

        def event_stream():
            client = get_redis_client()
            pubsub = client.pubsub()
            pubsub.subscribe(channel)

            try:
                yield ": connected\n\n"

                while True:
                    message = pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=15,
                    )

                    if message and message["type"] == "message":
                        payload = message["data"]
                        if isinstance(payload, bytes):
                            payload = payload.decode("utf-8")

                        json.loads(payload)
                        yield f"event: notification\ndata: {payload}\n\n"
                    else:
                        yield ": heartbeat\n\n"
            finally:
                pubsub.close()

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
