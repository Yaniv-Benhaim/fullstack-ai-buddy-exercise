from django.urls import path
from . import views

urlpatterns = [
    path("modules/", views.ModuleListView.as_view(), name="module-list"),
    path("progress/", views.UserProgressListView.as_view(), name="progress-list"),
    path(
        "progress/<int:pk>/",
        views.UserProgressUpdateView.as_view(),
        name="progress-update",
    ),
    path(
        "notifications/",
        views.NotificationListView.as_view(),
        name="notification-list",
    ),
]
