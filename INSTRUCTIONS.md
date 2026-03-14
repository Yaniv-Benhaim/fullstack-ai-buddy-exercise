# Exercise Instructions

## User Story

> *"As a Logistics Manager at Flying Cargo, I want to receive an AI-powered nudge after I finish a module that helps me hit my quarterly efficiency goals."*

The app skeleton is functional — modules load, progress can be tracked. But the AI nudge pipeline is disconnected across three "broken bridges." Your job is to wire them up end-to-end.

**Time target: ~45 minutes**

---

## Step 1 — Implement the Celery task (Bridge #1)

**File:** `backend/learning/tasks.py`

The `generate_ai_nudge(user_id, module_id)` task is empty. Implement it to:

1. Fetch the user's profile and the completed module from the database
2. Build a prompt that includes the module context, the user's skill gaps, and their quarterly goals
3. Call the LLM and extract the response
4. Save the response as a `Notification` so the frontend can display it

**Where to look:**
- `backend/learning/models.py` — the data model (UserProfile fields, Notification fields)
- `backend/config/settings.py` — `OLLAMA_BASE_URL` setting
- `backend/requirements.txt` — available packages (`openai`, `celery`, etc.)

**Ollama API reference:**

Ollama exposes an OpenAI-compatible endpoint. From inside Docker:
- Base URL: `http://ollama:11434/v1`
- Model: `tinyllama`
- No real API key required (any string works)

You can test it from your terminal:
```bash
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "tinyllama", "messages": [{"role": "user", "content": "hello"}]}'
```

---

## Step 2 — Wire up the trigger (Bridge #3)

**File:** `backend/learning/views.py`

In `UserProgressUpdateView`, the call to `generate_ai_nudge.delay()` is commented out. Uncomment it (and the import at the top of the file) so that completing a module triggers your task.

---

## Step 3 — Display nudges in the UI (Bridge #2)

**File:** `frontend/src/components/NudgeWidget.tsx`

The widget currently shows a static placeholder. Replace it with a real implementation that displays AI nudges from the backend.

**Choose a real-time strategy:**
- **Polling** (simplest) — a `useNotifications()` hook already exists in `hooks/useQueries.ts`
- **SSE** — add a server-sent events endpoint in Django and listen with `EventSource`
- **WebSockets** — add Django Channels

**Where to look:**
- `frontend/src/types.ts` — the `Notification` type
- `frontend/src/store/useStore.ts` — Zustand store with notifications state
- `frontend/src/hooks/useQueries.ts` — existing TanStack Query hooks

---

## Verify it works

1. Open http://localhost:5173
2. Click "Mark Complete" on a module
3. Wait a few seconds for the Celery task to run
4. An AI-generated nudge should appear in the widget

---

## API Reference

| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| GET    | `/api/modules/`       | List all learning modules      |
| GET    | `/api/progress/`      | Get user's progress records    |
| PATCH  | `/api/progress/{id}/` | Update progress (mark complete)|
| GET    | `/api/notifications/` | Get user's notifications       |

---

## Evaluation Criteria

- **Correctness** — Does the nudge pipeline work end-to-end?
- **Code quality** — Clean, readable, well-structured code
- **Prompt engineering** — Is the LLM prompt effective and contextual?
- **Frontend polish** — Good UX for displaying nudges
- **Architecture decisions** — Sensible choices for real-time strategy
