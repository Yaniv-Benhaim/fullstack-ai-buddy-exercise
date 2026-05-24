# AI Nudge Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Completing a learning module generates a contextual AI nudge through Celery/Ollama and displays it in the browser in real time.

**Architecture:** The backend stores notifications durably in PostgreSQL, publishes newly created notifications through Redis pub/sub, and streams live events to the browser with SSE. The frontend keeps its existing TanStack Query initial fetch and Zustand notification store, then appends live SSE notifications in `NudgeWidget`.

**Tech Stack:** Django 5.1, Django REST Framework, Celery, Redis, Ollama OpenAI-compatible API, React 18, TypeScript, Vite, TanStack Query, Zustand.

---

## File Structure

- Modify `backend/learning/tasks.py`: implement prompt construction, Ollama call, notification creation, Redis publish, and fallback notification behavior.
- Create `backend/learning/tests.py`: backend tests for nudge generation, fallback behavior, and progress completion trigger.
- Modify `backend/learning/views.py`: dispatch Celery task on new completion and add the SSE endpoint.
- Modify `backend/learning/urls.py`: route `/api/notifications/stream/`.
- Modify `frontend/src/store/useStore.ts`: dedupe live notifications by ID when adding.
- Modify `frontend/src/components/NudgeWidget.tsx`: open SSE connection, add live notifications to Zustand, and render latest nudge/fallback state.
- Create `DESIGN.md`: concise exercise-facing architecture note.

## Task 1: Backend AI Nudge Task

**Files:**
- Modify: `backend/learning/tasks.py`
- Create: `backend/learning/tests.py`

- [ ] **Step 1: Add failing tests for successful generation and fallback**

Create `backend/learning/tests.py` with:

```python
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from learning.models import Module, Notification, UserProfile, UserProgress
from learning.tasks import generate_ai_nudge


class GenerateAiNudgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        UserProfile.objects.create(
            user=self.user,
            skill_gaps=["fuel efficiency", "cargo load planning"],
            quarterly_goals=["Cut fuel costs by 10%", "95% on-time delivery"],
        )
        self.completed_module = Module.objects.create(
            name="Fuel Efficiency Best Practices",
            category="Operations",
            description="Reduce fuel use across the fleet.",
        )
        self.remaining_module = Module.objects.create(
            name="Cargo Loading Optimization",
            category="Operations",
            description="Improve load planning.",
        )
        UserProgress.objects.create(
            user=self.user,
            module=self.completed_module,
            status=UserProgress.Status.COMPLETED,
        )
        UserProgress.objects.create(
            user=self.user,
            module=self.remaining_module,
            status=UserProgress.Status.NOT_STARTED,
        )

    @patch("learning.tasks.publish_notification")
    @patch("learning.tasks.OpenAI")
    def test_generate_ai_nudge_saves_and_publishes_notification(
        self, mock_openai, mock_publish
    ):
        message = Mock(content="Great job connecting fuel efficiency to cost goals.")
        choice = Mock(message=message)
        completion = Mock(choices=[choice])
        mock_openai.return_value.chat.completions.create.return_value = completion

        notification_id = generate_ai_nudge(self.user.id, self.completed_module.id)

        notification = Notification.objects.get(id=notification_id)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, Notification.NotificationType.AI_NUDGE)
        self.assertEqual(
            notification.message,
            "Great job connecting fuel efficiency to cost goals.",
        )
        mock_publish.assert_called_once_with(notification)
        prompt = mock_openai.return_value.chat.completions.create.call_args.kwargs[
            "messages"
        ][1]["content"]
        self.assertIn("Fuel Efficiency Best Practices", prompt)
        self.assertIn("Cargo Loading Optimization", prompt)
        self.assertIn("Cut fuel costs by 10%", prompt)

    @override_settings(OLLAMA_BASE_URL="http://ollama:11434")
    @patch("learning.tasks.publish_notification")
    @patch("learning.tasks.OpenAI")
    def test_generate_ai_nudge_creates_fallback_when_ollama_fails(
        self, mock_openai, mock_publish
    ):
        mock_openai.return_value.chat.completions.create.side_effect = RuntimeError(
            "ollama unavailable"
        )

        notification_id = generate_ai_nudge(self.user.id, self.completed_module.id)

        notification = Notification.objects.get(id=notification_id)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, Notification.NotificationType.SYSTEM)
        self.assertIn("Nice work completing Fuel Efficiency Best Practices", notification.message)
        self.assertIn("could not generate", notification.message.lower())
        mock_publish.assert_called_once_with(notification)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
docker compose run --rm backend python manage.py test learning.tests.GenerateAiNudgeTests
```

Expected: FAIL because `publish_notification` and `OpenAI` are not defined in `learning.tasks`, and `generate_ai_nudge` returns `None`.

- [ ] **Step 3: Implement the Celery task**

Replace `backend/learning/tasks.py` with:

```python
import json
import logging

import redis
from celery import shared_task
from django.conf import settings
from openai import OpenAI

from .models import Module, Notification, UserProgress
from .serializers import NotificationSerializer

logger = logging.getLogger(__name__)


def get_redis_client():
    return redis.Redis.from_url(settings.CELERY_BROKER_URL)


def notification_channel(user_id: int) -> str:
    return f"notifications:user:{user_id}"


def publish_notification(notification: Notification) -> None:
    payload = NotificationSerializer(notification).data
    get_redis_client().publish(
        notification_channel(notification.user_id),
        json.dumps(payload, default=str),
    )


def build_progress_summary(progress_records) -> str:
    grouped = {
        UserProgress.Status.COMPLETED: [],
        UserProgress.Status.IN_PROGRESS: [],
        UserProgress.Status.NOT_STARTED: [],
    }

    for progress in progress_records:
        grouped[progress.status].append(progress.module.name)

    def format_group(label, items):
        value = ", ".join(items) if items else "none"
        return f"{label}: {value}"

    return "\n".join(
        [
            format_group("Completed modules", grouped[UserProgress.Status.COMPLETED]),
            format_group("In-progress modules", grouped[UserProgress.Status.IN_PROGRESS]),
            format_group("Not-started modules", grouped[UserProgress.Status.NOT_STARTED]),
        ]
    )


def build_nudge_prompt(user, module: Module, progress_records) -> str:
    profile = getattr(user, "profile", None)
    skill_gaps = ", ".join(profile.skill_gaps) if profile and profile.skill_gaps else "none"
    quarterly_goals = (
        ", ".join(profile.quarterly_goals)
        if profile and profile.quarterly_goals
        else "none"
    )
    progress_summary = build_progress_summary(progress_records)

    return (
        "You are an AI learning buddy for a logistics manager at Flying Cargo.\n"
        "Write one concise, encouraging nudge after the learner completes a module.\n"
        "Keep it under 80 words. Be specific, practical, and avoid generic praise.\n\n"
        f"Completed module: {module.name}\n"
        f"Module description: {module.description}\n"
        f"Quarterly goals: {quarterly_goals}\n"
        f"Skill gaps: {skill_gaps}\n"
        f"Learning progress:\n{progress_summary}\n\n"
        "Connect the completed module to one goal, skill gap, or next useful module."
    )


def create_fallback_notification(user, module: Module) -> Notification:
    profile = getattr(user, "profile", None)
    goal = (
        profile.quarterly_goals[0]
        if profile and profile.quarterly_goals
        else "your quarterly efficiency goals"
    )
    return Notification.objects.create(
        user=user,
        notification_type=Notification.NotificationType.SYSTEM,
        message=(
            f"Nice work completing {module.name}. I could not generate a personalized "
            f"AI nudge right now, but this module still supports {goal}."
        ),
    )


@shared_task
def generate_ai_nudge(user_id: int, module_id: int):
    """
    Generate an AI-powered nudge after a user completes a learning module.
    """
    module = Module.objects.get(id=module_id)
    progress_records = (
        UserProgress.objects.filter(user_id=user_id)
        .select_related("user", "user__profile", "module")
        .order_by("module__name")
    )
    user = progress_records[0].user if progress_records else module.progress.get(user_id=user_id).user

    try:
        client = OpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL.rstrip('/')}/v1",
            api_key="ollama",
            timeout=20,
        )
        completion = client.chat.completions.create(
            model="tinyllama",
            messages=[
                {
                    "role": "system",
                    "content": "You write concise workplace learning nudges.",
                },
                {"role": "user", "content": build_nudge_prompt(user, module, progress_records)},
            ],
            temperature=0.5,
            max_tokens=120,
        )
        message = completion.choices[0].message.content.strip()
        notification = Notification.objects.create(
            user=user,
            message=message,
            notification_type=Notification.NotificationType.AI_NUDGE,
        )
    except Exception:
        logger.exception("Failed to generate AI nudge for user=%s module=%s", user_id, module_id)
        notification = create_fallback_notification(user, module)

    publish_notification(notification)
    return notification.id
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
docker compose run --rm backend python manage.py test learning.tests.GenerateAiNudgeTests
```

Expected: PASS with both tests green.

- [ ] **Step 5: Commit task implementation**

Run:

```bash
git add backend/learning/tasks.py backend/learning/tests.py
git commit -m "Implement AI nudge generation task"
```

## Task 2: Completion Trigger

**Files:**
- Modify: `backend/learning/views.py`
- Modify: `backend/learning/tests.py`

- [ ] **Step 1: Add failing tests for task dispatch on new completion only**

Append to `backend/learning/tests.py`:

```python
from rest_framework.test import APIRequestFactory

from learning.views import UserProgressUpdateView


class ProgressCompletionTriggerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="trigger-user")
        self.module = Module.objects.create(
            name="Route Optimization Fundamentals",
            category="Operations",
            description="Improve route planning.",
        )
        self.progress = UserProgress.objects.create(
            user=self.user,
            module=self.module,
            status=UserProgress.Status.NOT_STARTED,
        )
        self.factory = APIRequestFactory()

    @patch("learning.views.generate_ai_nudge.delay")
    def test_dispatches_nudge_task_when_progress_becomes_completed(self, mock_delay):
        request = self.factory.patch(
            f"/api/progress/{self.progress.id}/",
            {"status": "completed"},
            format="json",
        )
        request.user = self.user

        response = UserProgressUpdateView.as_view()(request, pk=self.progress.id)

        self.assertEqual(response.status_code, 200)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, UserProgress.Status.COMPLETED)
        self.assertIsNotNone(self.progress.completed_at)
        mock_delay.assert_called_once_with(
            user_id=self.user.id,
            module_id=self.module.id,
        )

    @patch("learning.views.generate_ai_nudge.delay")
    def test_does_not_dispatch_when_progress_was_already_completed(self, mock_delay):
        self.progress.status = UserProgress.Status.COMPLETED
        self.progress.save(update_fields=["status"])
        request = self.factory.patch(
            f"/api/progress/{self.progress.id}/",
            {"status": "completed"},
            format="json",
        )
        request.user = self.user

        response = UserProgressUpdateView.as_view()(request, pk=self.progress.id)

        self.assertEqual(response.status_code, 200)
        mock_delay.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
docker compose run --rm backend python manage.py test learning.tests.ProgressCompletionTriggerTests
```

Expected: FAIL because `generate_ai_nudge` is not imported in `views.py` and the dispatch is still commented out.

- [ ] **Step 3: Implement completion trigger**

In `backend/learning/views.py`, add the import:

```python
from .tasks import generate_ai_nudge
```

Replace `perform_update` with:

```python
    def perform_update(self, serializer):
        previous_status = serializer.instance.status
        instance = serializer.save()

        became_completed = (
            previous_status != "completed" and instance.status == "completed"
        )

        if became_completed and instance.completed_at is None:
            instance.completed_at = timezone.now()
            instance.save(update_fields=["completed_at"])

        if became_completed:
            generate_ai_nudge.delay(
                user_id=instance.user.id,
                module_id=instance.module.id,
            )
```

- [ ] **Step 4: Run trigger tests**

Run:

```bash
docker compose run --rm backend python manage.py test learning.tests.ProgressCompletionTriggerTests
```

Expected: PASS.

- [ ] **Step 5: Commit trigger**

Run:

```bash
git add backend/learning/views.py backend/learning/tests.py
git commit -m "Trigger AI nudge when module is completed"
```

## Task 3: Redis-Backed SSE Endpoint

**Files:**
- Modify: `backend/learning/views.py`
- Modify: `backend/learning/urls.py`
- Modify: `backend/learning/tests.py`

- [ ] **Step 1: Add a URL test for the stream endpoint**

Append to `backend/learning/tests.py`:

```python
from django.urls import reverse


class NotificationStreamRouteTests(TestCase):
    def test_notification_stream_route_resolves(self):
        url = reverse("notification-stream")
        self.assertEqual(url, "/api/notifications/stream/")
```

- [ ] **Step 2: Run route test to verify it fails**

Run:

```bash
docker compose run --rm backend python manage.py test learning.tests.NotificationStreamRouteTests
```

Expected: FAIL because the route name does not exist.

- [ ] **Step 3: Add SSE view**

In `backend/learning/views.py`, add imports:

```python
import json

from django.http import StreamingHttpResponse
```

Add this view below `NotificationListView`:

```python
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
```

- [ ] **Step 4: Add SSE URL**

In `backend/learning/urls.py`, add before the plain notifications route or immediately after it:

```python
    path(
        "notifications/stream/",
        views.NotificationStreamView.as_view(),
        name="notification-stream",
    ),
```

- [ ] **Step 5: Run route test**

Run:

```bash
docker compose run --rm backend python manage.py test learning.tests.NotificationStreamRouteTests
```

Expected: PASS.

- [ ] **Step 6: Run all backend tests**

Run:

```bash
docker compose run --rm backend python manage.py test learning
```

Expected: PASS.

- [ ] **Step 7: Commit SSE endpoint**

Run:

```bash
git add backend/learning/views.py backend/learning/urls.py backend/learning/tests.py
git commit -m "Add Redis backed notification stream"
```

## Task 4: Frontend Live Nudge Widget

**Files:**
- Modify: `frontend/src/store/useStore.ts`
- Modify: `frontend/src/components/NudgeWidget.tsx`

- [ ] **Step 1: Add dedupe to notification store**

Replace `addNotification` in `frontend/src/store/useStore.ts` with:

```typescript
  addNotification: (notification) =>
    set((state) => {
      if (state.notifications.some((item) => item.id === notification.id)) {
        return state;
      }

      return {
        notifications: [notification, ...state.notifications],
      };
    }),
```

- [ ] **Step 2: Replace placeholder widget with SSE-powered widget**

Replace `frontend/src/components/NudgeWidget.tsx` with:

```typescript
import { useEffect, useMemo, useState } from "react";
import { Bot, WifiOff } from "lucide-react";
import { useStore } from "../store/useStore";
import type { Notification } from "../types";

export default function NudgeWidget() {
  const { notifications, addNotification } = useStore();
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const source = new EventSource("/api/notifications/stream/");

    source.onopen = () => {
      setIsConnected(true);
    };

    source.addEventListener("notification", (event) => {
      const notification = JSON.parse(event.data) as Notification;
      addNotification(notification);
    });

    source.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      source.close();
    };
  }, [addNotification]);

  const latestNudge = useMemo(
    () =>
      notifications.find(
        (notification) =>
          notification.notification_type === "ai_nudge" ||
          notification.notification_type === "system"
      ),
    [notifications]
  );

  return (
    <div className="fixed bottom-4 right-4 max-w-sm w-[calc(100%-2rem)] bg-white border border-gray-200 rounded-xl shadow-lg p-4">
      <div className="flex items-start gap-3">
        <div className="w-9 h-9 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
          <Bot className="w-5 h-5 text-blue-600" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <h4 className="font-medium text-gray-900 text-sm">AI Nudge</h4>
            {!isConnected && (
              <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                <WifiOff className="w-3 h-3" />
                Reconnecting
              </span>
            )}
          </div>
          <p className="text-sm text-gray-600 mt-1">
            {latestNudge
              ? latestNudge.message
              : "Complete a module to receive a contextual learning nudge."}
          </p>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Run frontend build**

Run:

```bash
docker compose run --rm frontend npm run build
```

Expected: PASS with TypeScript and Vite build succeeding.

- [ ] **Step 4: Commit frontend live widget**

Run:

```bash
git add frontend/src/store/useStore.ts frontend/src/components/NudgeWidget.tsx
git commit -m "Display live AI nudges"
```

## Task 5: Exercise DESIGN.md

**Files:**
- Create: `DESIGN.md`

- [ ] **Step 1: Create concise exercise design note**

Create `DESIGN.md` with:

```markdown
# Design

## Real-Time Strategy

I used Server-Sent Events for browser delivery and Redis pub/sub for backend fanout. The app only needs one-way updates from the server to the browser when a notification is created, so SSE keeps the browser integration simple while still satisfying the real-time requirement.

The Celery task creates the notification in PostgreSQL first, then publishes the serialized notification to a Redis channel scoped to the user. The SSE endpoint subscribes to that channel and streams notification events to the frontend. The existing `/api/notifications/` endpoint remains the durable source of truth for initial load and refresh recovery.

## Tradeoff

Redis pub/sub messages are ephemeral. If the browser is disconnected at the exact moment a notification is published, it can miss the live event. That is acceptable for this exercise because every notification is also stored in the database and fetched on page load.

## With More Time

I would add `Last-Event-ID` replay support or move the event layer to Django Channels if the app needed stronger delivery guarantees, multiple concurrent users, or bidirectional interactions. I would also add mark-as-read behavior and a notification history panel.
```

- [ ] **Step 2: Commit design note**

Run:

```bash
git add DESIGN.md
git commit -m "Document AI nudge design"
```

## Task 6: End-to-End Verification

**Files:**
- No planned file changes.

- [ ] **Step 1: Start the stack**

Run:

```bash
docker compose up --build
```

Expected:

- `backend` runs migrations and seeds data.
- `celery` starts and connects to Redis.
- `ollama` starts and pulls/serves `tinyllama`.
- `frontend` serves Vite at `http://localhost:5173`.

- [ ] **Step 2: Verify backend tests**

In another terminal, run:

```bash
docker compose exec backend python manage.py test learning
```

Expected: PASS.

- [ ] **Step 3: Verify frontend build**

Run:

```bash
docker compose exec frontend npm run build
```

Expected: PASS.

- [ ] **Step 4: Verify live nudge manually**

Open `http://localhost:5173`, click `Mark Complete` on a module, and wait a few seconds.

Expected:

- The progress count updates.
- Celery logs show `generate_ai_nudge` running.
- `NudgeWidget` updates without a browser refresh.
- The notification remains visible after refreshing because it was stored in PostgreSQL.

- [ ] **Step 5: Verify fallback behavior**

Temporarily stop Ollama:

```bash
docker compose stop ollama
```

Mark another incomplete module complete.

Expected:

- A fallback notification appears.
- The UI does not silently fail.
- Celery logs include the Ollama exception.

Restart Ollama:

```bash
docker compose start ollama
```

- [ ] **Step 6: Final status check**

Run:

```bash
git status --short
```

Expected: only intentional changes remain, plus the pre-existing `.env.example` deletion if it has not been handled separately.
