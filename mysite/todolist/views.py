from django.shortcuts import redirect, get_object_or_404
from django.views import generic

from .models import Task, TaskForm

class IndexView(generic.ListView):
    template_name = 'todolist/index.html'

    def get_queryset(self):
        task_list = Task.objects.prefetch_related('group').all()

        for task in task_list:
            group_names = [group.name for group in task.group.all()[:3]]
            task.group_names = " - ".join(group_names)

        return task_list
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_form'] = TaskForm()
        return context

class DetailView(generic.DetailView):
    model = Task
    template_name = 'todolist/detail.html'

    def get_object(self, queryset=None):
        task = super(DetailView, self).get_object(queryset=queryset)
        group_names = [group.name for group in task.group.all()[:3]]
        task.group_names = " - ".join(group_names)

        return task
    
def CompleteTask(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    task.delete()
    return redirect('todolist:index')

def CreateTask(request):
    pass
