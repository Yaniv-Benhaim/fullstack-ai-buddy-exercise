# AI Nudge Pipeline Design

## Goal

Wire the existing Flying Cargo learning app so that completing a module creates a contextual AI nudge and displays it in the browser in real time.

The solution should be exercise-optimized but clean: fast to implement, easy to explain, and built from infrastructure already present in the project.

## Chosen Approach

Use Celery for asynchronous nudge generation, Ollama for the local LLM call, PostgreSQL for durable notification storage, Redis pub/sub for notification fanout, and Server-Sent Events for browser delivery.

This keeps the design small:

- Celery already exists for background tasks.
- Redis already exists as the Celery broker/result backend.
- The browser only needs one-way updates from the server, so SSE is simpler than WebSockets.
- Existing `/api/notifications/` remains the durable source of truth.

## Data Flow

1. The frontend sends `PATCH /api/progress/{id}/` with `status: "completed"`.
2. `UserProgressUpdateView` saves the new status and sets `completed_at` if needed.
3. If this is a new transition into `completed`, the view dispatches `generate_ai_nudge.delay(user_id, module_id)`.
4. The Celery task loads the user, completed module, user profile, and all user progress records.
5. The task builds a compact context summary:
   - completed modules
   - in-progress modules
   - not-started modules
   - quarterly goals
   - skill gaps
6. The task calls Ollama through the OpenAI-compatible chat completions API using `tinyllama`.
7. The task saves a `Notification` row with the generated nudge.
8. The task publishes the serialized notification to Redis channel `notifications:user:{user_id}`.
9. The frontend keeps an `EventSource` connection to `/api/notifications/stream/`.
10. The SSE endpoint subscribes to the same Redis channel and streams each message to the browser.
11. The frontend adds the notification to Zustand and renders it in `NudgeWidget`.

## Backend Components

### Celery Task

`backend/learning/tasks.py` will own nudge generation.

Responsibilities:

- Query the needed learning context.
- Build the prompt.
- Call Ollama with a bounded timeout.
- Save a notification whether generation succeeds or fails.
- Publish the saved notification to Redis.

The task should keep the prompt practical and short. The nudge should mention the completed module and connect it to either quarterly goals, skill gaps, or remaining modules.

### Progress Update Trigger

`backend/learning/views.py` will dispatch the task after a module transitions into `completed`.

The trigger should compare the previous status to the new status so repeated updates to an already completed module do not generate duplicate nudges.

### SSE Endpoint

`backend/learning/views.py` will expose a streaming endpoint, for example:

`GET /api/notifications/stream/`

Responsibilities:

- Identify the current auto-authenticated user.
- Subscribe to `notifications:user:{user_id}`.
- Emit Redis messages as SSE `notification` events.
- Send lightweight heartbeat comments to keep the connection alive.
- Close cleanly when the browser disconnects.

The endpoint does not replace `/api/notifications/`; it only provides live delivery.

## Frontend Components

### Notification State

The existing Zustand store remains the shared notification state. Initial notifications still come from the existing TanStack Query fetch.

When a live SSE event arrives, the frontend calls `addNotification(notification)`.

### Nudge Widget

`frontend/src/components/NudgeWidget.tsx` will become the live display surface.

Responsibilities:

- Open an `EventSource` to `/api/notifications/stream/`.
- Parse incoming notification events.
- Add notifications to the store.
- Render the newest AI nudge.
- Show a calm placeholder when there are no nudges yet.
- Let the browser's built-in `EventSource` reconnect behavior handle transient disconnects.

## Error Handling

If Ollama is unavailable, slow, or returns an invalid response, the Celery task should still create a useful fallback notification. The user should receive feedback instead of silence.

Example fallback behavior:

> Nice work completing Fuel Efficiency Best Practices. I could not generate a personalized AI nudge right now, but this module still supports your goal to cut fuel costs by 10%.

The task should log the original exception for debugging but avoid exposing technical error details in the user-facing message.

If SSE disconnects, the frontend does not need a loud error state. `EventSource` reconnects automatically, and `/api/notifications/` remains available for durable notification recovery on reload.

## Tradeoffs

Redis pub/sub is fast and already available, but messages are ephemeral. If the browser is disconnected at the exact moment Celery publishes, the live event can be missed.

That is acceptable for this exercise because notifications are also saved in PostgreSQL and fetched through `/api/notifications/`. With more time, the stream could support replay by `Last-Event-ID`, or the architecture could move to Django Channels with a more robust event layer.

## Verification

Manual verification should follow the exercise flow:

1. Start the stack with Docker Compose.
2. Open `http://localhost:5173`.
3. Click `Mark Complete` on a module.
4. Confirm the progress updates.
5. Wait for Celery to call Ollama.
6. Confirm a nudge appears in `NudgeWidget` without refreshing.
7. Stop or break Ollama and confirm a fallback notification appears instead of silent failure.

Developer checks should include:

- Backend import/check command if available.
- Frontend TypeScript build.
- A quick browser run through the completion flow.

## Out Of Scope

- User login or multi-user account management.
- Mark-as-read behavior.
- Notification history UI beyond the latest nudge widget.
- WebSocket infrastructure.
- Sophisticated learning analytics.
- Prompt evaluation harness.
