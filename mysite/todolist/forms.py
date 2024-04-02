from django.forms import ModelForm, CharField, DateTimeInput, PasswordInput, TextInput
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import Task

class TaskForm(ModelForm):
    deadline = CharField(widget=DateTimeInput(attrs={'type':'datetime-local'}))

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
    password = CharField(widget=PasswordInput)