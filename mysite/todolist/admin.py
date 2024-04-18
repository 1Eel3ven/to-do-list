from django.contrib import admin

from .models import Task, TaskGroup, CompletedTask

admin.site.register(Task)
admin.site.register(TaskGroup)
admin.site.register(CompletedTask)
