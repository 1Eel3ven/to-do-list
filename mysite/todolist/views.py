from django.shortcuts import render, redirect, get_object_or_404, HttpResponseRedirect
from django.http import Http404
from django.views import generic
from django.urls import reverse

from django.contrib.auth.models import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate

from .models import Task, TaskGroup
from .forms import TaskForm, GroupForm, LoginForm, CreateUserForm

class IndexView(generic.ListView):
    template_name = 'todolist/index.html'

    def get_queryset(self):
        user_id = self.request.user.id
        task_list = Task.objects.prefetch_related('group').filter(owner_id=user_id)

        for task in task_list:
            group_names = [group.name for group in task.group.filter(owner_id=user_id)[:3]]
            task.group_names = " - ".join(group_names)

        return task_list
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_form'] = TaskForm(user=self.request.user)
        return context

class DetailView(generic.DetailView):
    model = Task
    template_name = 'todolist/detail.html'

    def get_object(self, queryset=None):
        try:
            task = super(DetailView, self).get_object(queryset=queryset)
        except:
            raise Http404('Task doesnt exist')
        else:
            if task.owner_id != self.request.user.id:
                raise Http404('Task doesnt exist')

        group_names = [group.name for group in task.group.all()[:3]]
        task.group_names = " - ".join(group_names)

        return task
    
def CompleteTask(request, task_id):
    try:
        task = Task.objects.get(pk=task_id, owner_id=request.user.id)
    except:
        raise Http404('Task doesnt exist')
    
    task.delete()
    return redirect('todolist:index')

class EditView(generic.DetailView):
    model = Task
    queryset = Task.objects.all()
    template_name = 'todolist/edit.html'

    def get_context_data(self, **kwargs):
        user = self.request.user

        context = super().get_context_data(**kwargs)
        task = get_object_or_404(Task, pk=self.kwargs['pk'], owner_id=user.id)
        context['task_form'] = TaskForm(instance=task, user=user)
        return context

@login_required    
def EditTask(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner_id=request.user.id)

    if request.method == "POST":
        form = TaskForm(request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            groups = cleaned_data.pop('group') # Removing many-to-many field from cleaned_data

            Task.objects.filter(pk=task_id).update(**cleaned_data)

            task = Task.objects.get(pk=task_id)
            task.group.set(groups)
            task.save()

        return HttpResponseRedirect(reverse('todolist:index'))

@login_required
def CreateTask(request):
    if request.method == "POST":
        form = TaskForm(request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            groups = cleaned_data.pop('group')

            new_task = Task.objects.create(**cleaned_data)
            new_task.group.set(groups)
            new_task.owner_id = request.user.id
            new_task.save()

    return HttpResponseRedirect(reverse('todolist:index'))

@login_required
def AddGroup(request):
    if request.method == "POST":

        group_name = request.POST.get('group_name')
        new_group = TaskGroup.objects.create(name=group_name)
        new_group.owner_id = request.user.id
        new_group.save()

    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def DeleteGroup(request):
    if request.method == "POST":

        form = GroupForm(request.POST)

        if form.is_valid():
            selected_groups = form.cleaned_data['group']

            for group in selected_groups:
                TaskGroup.objects.get(name=group.name, owner_id = request.user.id).delete()

    return redirect(request.META.get('HTTP_REFERER', '/'))


def RegisterView(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect(reverse('todolist:login'))

    context = {'register_form': CreateUserForm}

    return render(request, 'todolist/register.html', context=context)

def LoginView(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth.login(request, user)

                return redirect(reverse('todolist:index'))

    context = {'login_form': LoginForm}

    return render(request, 'todolist/login.html', context=context)

def LogOutView(request):
    auth.logout(request)

    return redirect(reverse('todolist:index'))