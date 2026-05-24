import json
import logging

import httpx
import redis
from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User

from .models import Module, Notification, UserProgress
from .serializers import NotificationSerializer


logger = logging.getLogger(__name__)


def get_redis_client():
    return redis.Redis.from_url(settings.CELERY_BROKER_URL)


def notification_channel(user_id):
    return f"notifications:user:{user_id}"


def publish_notification(notification):
    serializer = NotificationSerializer(notification)
    payload = json.dumps(serializer.data, default=str)
    get_redis_client().publish(notification_channel(notification.user_id), payload)


def build_progress_summary(progress_records):
    summary = {
        UserProgress.Status.COMPLETED: [],
        UserProgress.Status.IN_PROGRESS: [],
        UserProgress.Status.NOT_STARTED: [],
    }

    for progress in progress_records:
        summary.setdefault(progress.status, []).append(progress.module.name)

    return {
        "completed": summary[UserProgress.Status.COMPLETED],
        "in_progress": summary[UserProgress.Status.IN_PROGRESS],
        "not_started": summary[UserProgress.Status.NOT_STARTED],
    }


def _format_list(values):
    return ", ".join(values) if values else "None listed"


def build_nudge_prompt(user, module, progress_records):
    profile = getattr(user, "profile", None)
    quarterly_goals = getattr(profile, "quarterly_goals", [])
    skill_gaps = getattr(profile, "skill_gaps", [])
    progress_summary = build_progress_summary(progress_records)

    return (
        f"User {user.username} just completed module: {module.name}.\n"
        f"Completed module description: {module.description}\n"
        f"Quarterly goals: {_format_list(quarterly_goals)}\n"
        f"Skill gaps: {_format_list(skill_gaps)}\n"
        "Progress summary:\n"
        f"- Completed: {_format_list(progress_summary['completed'])}\n"
        f"- In progress: {_format_list(progress_summary['in_progress'])}\n"
        f"- Not started: {_format_list(progress_summary['not_started'])}\n"
        "Write a useful, motivating next-step learning nudge under 80 words."
    )


def create_fallback_notification(user, module):
    return Notification.objects.create(
        user=user,
        notification_type=Notification.NotificationType.SYSTEM,
        message=(
            f"Nice work completing {module.name}. Keep momentum by choosing your "
            "next learning module and focusing on one practical improvement today."
        ),
    )


def generate_with_ollama(prompt):
    response = httpx.post(
        f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
        json={
            "model": "tinyllama",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.5,
                "num_predict": 60,
            },
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


@shared_task
def generate_ai_nudge(user_id: int, module_id: int):
    """
    Generate an AI-powered nudge after a user completes a learning module.
    """
    user = User.objects.select_related("profile").get(id=user_id)
    module = Module.objects.get(id=module_id)

    try:
        progress_records = list(
            UserProgress.objects.filter(user=user).select_related("module")
        )
        prompt = build_nudge_prompt(user, module, progress_records)
        message = generate_with_ollama(prompt)
        notification = Notification.objects.create(
            user=user,
            message=message,
            notification_type=Notification.NotificationType.AI_NUDGE,
        )
    except Exception:
        logger.exception(
            "Failed to generate AI nudge for user_id=%s module_id=%s",
            user_id,
            module_id,
        )
        notification = create_fallback_notification(user, module)

    publish_notification(notification)
    return notification.id
