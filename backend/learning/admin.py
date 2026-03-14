from django.contrib import admin
from .models import UserProfile, Module, UserProgress, Notification

admin.site.register(UserProfile)
admin.site.register(Module)
admin.site.register(UserProgress)
admin.site.register(Notification)
