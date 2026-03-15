# Exercise Instructions

## User Story

> *"As a Logistics Manager at Flying Cargo, I want to receive an AI-powered nudge after I finish a module that helps me hit my quarterly efficiency goals."*

The app skeleton is functional — modules load, progress can be tracked. But the AI nudge pipeline is disconnected. Your job is to wire it up end-to-end.

**Time target: ~45 minutes**

---

## Step 1 — Implement the AI nudge task and wire it up

**File:** `backend/learning/tasks.py`

The `generate_ai_nudge(user_id, module_id)` Celery task is empty. Implement it so that when a user completes a module, the LLM generates a personalized nudge and saves it as a notification.

The trigger in `backend/learning/views.py` is commented out — uncomment it once your task is ready.

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

## Step 2 — Display nudges in real time

**Files:** `frontend/src/components/NudgeWidget.tsx`, `backend/learning/views.py`

The nudge widget currently shows a static placeholder. Make nudges appear in real time when the Celery task completes.

This requires work on **both** backend and frontend — you'll need a way to push new notifications from the server to the browser.

Choose your approach (SSE, WebSockets).

---

## Step 3 — Handle errors gracefully

What happens if Ollama is slow or unavailable? Make sure the app handles this gracefully — the user should get appropriate feedback rather than a silent failure.

---

## Step 4 — Write DESIGN.md

Create a short `DESIGN.md` (a few paragraphs is fine) covering:

- Which real-time strategy you chose and why
- One tradeoff of your approach
- What you'd do differently with more time

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
- **Error handling** — Graceful behavior when things go wrong
- **Architecture decisions** — Sensible choices and clear reasoning in DESIGN.md
