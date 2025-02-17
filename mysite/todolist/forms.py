from django.forms import ModelForm, CharField, DateTimeInput, PasswordInput, TextInput
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from django.utils import timezone
from datetime import timedelta

from .models import Task, TaskGroup

class TaskForm(ModelForm):
    # make default deadline value for the form the end of current day
    tomorrow = timezone.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
    deadline = CharField(widget=DateTimeInput(attrs={'type':'datetime-local'}), initial=tomorrow)

    # when form is created, filter the available groups to those that belong to given user
    def __init__(self, *args, user=None, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)

        if user:
            self.fields['group'].queryset = TaskGroup.objects.filter(owner_id=user.id).distinct()

    class Meta:
        model = Task
        fields = ['name', 'description', 'priority', 'deadline', 'group']

class GroupForm(ModelForm):
    class Meta:
        model = Task
        fields = ['group']

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(AuthenticationForm):
    username = CharField(widget=TextInput())
    password = CharField(widget=PasswordInput())