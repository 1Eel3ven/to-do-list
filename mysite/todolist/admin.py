from django.contrib import admin
from django.urls import reverse

from .models import Task, TaskGroup, CompletedTask
from .views import make_completed_task_record


@admin.action(description='Complete selected tasks')
def complete_task(modeladmin, request, queryset):
    '''Makes completed task records for selected tasks'''
    for task in queryset:
        make_completed_task_record(task)
        task.delete()


class TaskTaskGroupIntermediaryInline(admin.TabularInline):
    model = Task.group.through
    extra = 0

class TaskGroupInline(TaskTaskGroupIntermediaryInline):
    verbose_name = 'Group'

class TaskInline(TaskTaskGroupIntermediaryInline):
    verbose_name = 'Task'


class TaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'deadline', 'is_outdated']
    list_filter = ['deadline']
    search_fields = ['name']
    actions = [complete_task]

    fieldsets = [(None, {'fields': ['name']}), 
                 ('Information', {'fields': ['description', 'priority'], 'classes': ['collapse']}), 
                 ('Date information', {'fields': ['deadline'], 'classes': ['collapse']}), 
                 ('Owner', {'fields': ['owner']}), 
                 ]
    
    inlines = [TaskGroupInline]

    def view_on_site(self, obj):
        url = reverse('todolist:detail', args=[obj.pk])
        return url

class TaskGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner']
    search_fields = ['name']

    fieldsets = [(None, {'fields': ['name']}), 
                 ('Owner', {'fields': ['owner']}), 
                 ]
    
    inlines = [TaskInline]

class CompletedTaskAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner']
    search_fields = ['name']

    fieldsets = [(None, {'fields': ['name']}), 
                 ('Owner', {'fields': ['owner']}), 
                 ]

admin.site.register(Task, TaskAdmin)
admin.site.register(TaskGroup, TaskGroupAdmin)
admin.site.register(CompletedTask, CompletedTaskAdmin)
