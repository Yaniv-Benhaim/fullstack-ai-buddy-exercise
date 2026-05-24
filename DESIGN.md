# Design

## Real-Time Strategy

I used Server-Sent Events for browser delivery and Redis pub/sub for backend fanout. The app only needs one-way updates from the server to the browser when a notification is created, so SSE keeps the browser integration simple while still satisfying the real-time requirement.

The Celery task creates the notification in PostgreSQL first, then publishes the serialized notification to a Redis channel scoped to the user. The SSE endpoint subscribes to that channel and streams notification events to the frontend. The existing `/api/notifications/` endpoint remains the durable source of truth for initial load and refresh recovery.

## Tradeoff

Redis pub/sub messages are ephemeral. If the browser is disconnected at the exact moment a notification is published, it can miss the live event. That is acceptable for this exercise because every notification is also stored in the database and fetched on page load.

## With More Time

I would add `Last-Event-ID` replay support or move the event layer to Django Channels if the app needed stronger delivery guarantees, multiple concurrent users, or bidirectional interactions. I would also add mark-as-read behavior and a notification history panel.
