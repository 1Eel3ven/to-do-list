from django.contrib import admin

from .models import Task, TaskGroup

admin.site.register(Task)
admin.site.register(TaskGroup)
