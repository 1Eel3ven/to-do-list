from django.shortcuts import render
from django.views import generic

from .models import Task

class IndexView(generic.ListView):
    template_name = 'todolist/index.html'

    def get_queryset(self):
        task_list = Task.objects.prefetch_related('group').all()

        for task in task_list:
            group_names = [group.name for group in task.group.all()[:3]]
            task.group_names = " - ".join(group_names)

        return task_list

class DetailView(generic.DetailView):
    model = Task
    template_name = 'todolist/detail.html'

    def get_object(self, queryset=None):
        task = super(DetailView, self).get_object(queryset=queryset)
        group_names = [group.name for group in task.group.all()[:3]]
        task.group_names = " - ".join(group_names)

        return task
