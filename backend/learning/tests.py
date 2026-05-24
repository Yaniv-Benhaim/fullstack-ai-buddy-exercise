from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Module, Notification, UserProfile, UserProgress
from .tasks import build_nudge_prompt, generate_ai_nudge


class GenerateAiNudgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        UserProfile.objects.create(
            user=self.user,
            skill_gaps=["fuel efficiency", "cargo load planning"],
            quarterly_goals=["Improve route efficiency by 15%"],
        )
        self.completed_module = Module.objects.create(
            name="Route Optimization",
            category="Operations",
            description="Plan efficient routes across changing delivery constraints.",
        )
        self.remaining_module = Module.objects.create(
            name="Fuel Efficiency",
            category="Operations",
            description="Reduce idle time and unnecessary fuel use.",
        )
        UserProgress.objects.create(
            user=self.user,
            module=self.completed_module,
            status=UserProgress.Status.COMPLETED,
            score=91,
        )
        UserProgress.objects.create(
            user=self.user,
            module=self.remaining_module,
            status=UserProgress.Status.NOT_STARTED,
        )

    def test_successful_ai_nudge_generation_saves_notification_and_publishes(self):
        with patch(
            "learning.tasks.generate_with_ollama",
            return_value="Keep momentum with Fuel Efficiency next.",
        ), patch(
            "learning.tasks.publish_notification"
        ) as publish_notification:
            notification_id = generate_ai_nudge(self.user.id, self.completed_module.id)

        notification = Notification.objects.get(id=notification_id)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.notification_type, Notification.NotificationType.AI_NUDGE
        )
        self.assertEqual(
            notification.message, "Keep momentum with Fuel Efficiency next."
        )
        publish_notification.assert_called_once_with(notification)

    def test_generated_prompt_includes_required_context(self):
        progress_records = list(
            UserProgress.objects.filter(user=self.user).select_related("module")
        )

        prompt = build_nudge_prompt(self.user, self.completed_module, progress_records)

        self.assertIn("Route Optimization", prompt)
        self.assertIn("Fuel Efficiency", prompt)
        self.assertIn("Improve route efficiency by 15%", prompt)
        self.assertIn("under 80 words", prompt)

    def test_ollama_failure_creates_fallback_notification_and_still_publishes(self):
        with patch(
            "learning.tasks.generate_with_ollama",
            side_effect=RuntimeError("ollama unavailable"),
        ), patch(
            "learning.tasks.publish_notification"
        ) as publish_notification, patch("learning.tasks.logger") as logger:
            notification_id = generate_ai_nudge(self.user.id, self.completed_module.id)

        notification = Notification.objects.get(id=notification_id)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(
            notification.notification_type, Notification.NotificationType.SYSTEM
        )
        self.assertIn(self.completed_module.name, notification.message)
        self.assertTrue(notification.message)
        publish_notification.assert_called_once_with(notification)
        logger.exception.assert_called_once()


class UserProgressCompletionTriggerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="learner")
        self.client.force_authenticate(user=self.user)
        self.module = Module.objects.create(
            name="Route Optimization",
            category="Operations",
            description="Plan efficient routes across changing delivery constraints.",
        )

    def test_completion_transition_sets_completed_at_and_triggers_ai_nudge(self):
        progress = UserProgress.objects.create(
            user=self.user,
            module=self.module,
            status=UserProgress.Status.NOT_STARTED,
        )

        with patch("learning.views.generate_ai_nudge.delay") as delay:
            response = self.client.patch(
                reverse("progress-update", args=[progress.id]),
                {"status": UserProgress.Status.COMPLETED},
                format="json",
            )

        progress.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(progress.status, UserProgress.Status.COMPLETED)
        self.assertIsNotNone(progress.completed_at)
        delay.assert_called_once_with(user_id=self.user.id, module_id=self.module.id)

    def test_repatching_completed_progress_does_not_trigger_ai_nudge(self):
        progress = UserProgress.objects.create(
            user=self.user,
            module=self.module,
            status=UserProgress.Status.COMPLETED,
        )

        with patch("learning.views.generate_ai_nudge.delay") as delay:
            response = self.client.patch(
                reverse("progress-update", args=[progress.id]),
                {"status": UserProgress.Status.COMPLETED},
                format="json",
            )

        self.assertEqual(response.status_code, 200)
        delay.assert_not_called()
