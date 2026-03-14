from rest_framework import serializers
from .models import Module, UserProgress, Notification


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ["id", "name", "category", "description"]


class UserProgressSerializer(serializers.ModelSerializer):
    module = ModuleSerializer(read_only=True)

    class Meta:
        model = UserProgress
        fields = ["id", "module", "status", "score", "completed_at"]
        read_only_fields = ["completed_at"]


class UserProgressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProgress
        fields = ["id", "status", "score"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "notification_type", "is_read", "created_at"]
