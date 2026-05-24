# Design

## Real-Time Strategy

I used Server-Sent Events for browser delivery and Redis pub/sub for backend fanout. 
The app only needs one-way updates from the server to the browser when a notification is created, so SSE keeps the browser integration simple while still satisfying the real-time requirement.

The Celery task creates the notification in PostgreSQL first, then publishes the serialized notification to a Redis channel scoped to the user. The SSE endpoint subscribes to that channel and streams notification events to the frontend. The existing `/api/notifications/` endpoint remains the durable source of truth for initial load and refresh recovery.

## Tradeoff

Redis pub/sub messages are ephemeral. If the browser is disconnected at the exact moment a notification is published, it can miss the live event. That is acceptable for this exercise because every notification is also stored in the database and fetched on page load.

## With More Time

For FrontEnd

Extract notification subscribing to a custom hook useNotifications
Instead of implementing it directly in the NudgeWidget ( )

Handling opening notifications when clicked showing a clean modal with more extended
information.

Disable the first notification on load with no relevant information.

When a notification gets closed remove the number bubble on the notification bell
Or atleast reduce by 1.




For backend.

1. Make the notification more personalized with a more detailed personal info
and process panel when the notification is opened.

2. Include a custom and unique call to action with a next suggestion for the 
user to take the next step in its process.

I would add `Last-Event-ID` replay support or move the event layer to Django Channels if the app needed stronger delivery guarantees, multiple concurrent users, or bidirectional interactions. 
I would also add mark-as-read behavior and a notification history panel.
