from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    skill_gaps = models.JSONField(default=list)
    quarterly_goals = models.JSONField(default=list)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Module(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name


class UserProgress(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="progress")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED
    )
    score = models.IntegerField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "module")
        verbose_name_plural = "User progress"

    def __str__(self):
        return f"{self.user.username} — {self.module.name} ({self.status})"


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        AI_NUDGE = "ai_nudge", "AI Nudge"
        SYSTEM = "system", "System"

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.AI_NUDGE,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.notification_type}] {self.message[:50]}"
