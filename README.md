# Flying Cargo — AI Learning Buddy Exercise

A full-stack coding exercise. See **[INSTRUCTIONS.md](INSTRUCTIONS.md)** for the exercise tasks.

## Quick Start

```bash
# 1. Copy the env file
cp .env.example .env

# 2. Start everything (first run pulls images & models — may take a few minutes)
docker compose up --build
```

Once running:

| Service   | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:5173         |
| Backend   | http://localhost:8000/api/    |
| Ollama    | http://localhost:11434        |

No API keys needed — Ollama runs locally inside Docker.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend   │────▶│   Backend    │────▶│ PostgreSQL  │
│  React/Vite  │     │  Django/DRF  │     │  :5432      │
│  :5173       │     │  :8000       │     └─────────────┘
└─────────────┘     └──────┬───────┘
                           │
                    ┌──────▼───────┐     ┌─────────────┐
                    │    Celery     │────▶│   Ollama     │
                    │    Worker     │     │   (LLM)     │
                    └──────┬───────┘     │  :11434      │
                           │             └─────────────┘
                    ┌──────▼───────┐
                    │    Redis      │
                    │   (Broker)    │
                    │   :6379       │
                    └──────────────┘
```

## Tech Stack

| Layer    | Technology                          |
|----------|-------------------------------------|
| Frontend | React 18, Vite, TypeScript, Tailwind, TanStack Query, Zustand |
| Backend  | Django 5.1, Django REST Framework   |
| Tasks    | Celery + Redis                      |
| LLM      | Ollama (tinyllama)                  |
| Database | PostgreSQL 16                       |

## Seed Data

The app auto-seeds on startup with:

- **User**: `testuser` / `testpass123`
- **Profile**: skill gaps in route optimization, fuel efficiency, cargo load planning
- **5 Modules**: Route Optimization, Warehouse Safety, Fleet GPS, Fuel Efficiency, Cargo Loading
