from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from .models import Task, TaskGroup

def create_task(task_name, days=5, groups=None, user=None):
    '''Creates a task with deadline offset to now;
    Negative for task with deadline in the past; Positive for task with deadline in the future.'''
    time = timezone.now() + timedelta(days=days)
    task = Task.objects.create(name=task_name, deadline=time)

    if groups:
        for g in groups:
            task.group.add(g)

    if user:
        task.owner_id = user.id

    return task

def create_group(group_name, user=None):
    group = TaskGroup.objects.create(name=group_name)

    if user:
        group.owner_id = user.id

    return group


class IndexTaskViewTests(TestCase):
    def setUp(self):
        self.c = Client()

    def test_no_tasks(self):
        '''Testing if an appropriate message displayed when no tasks exist'''
        response = self.c.get(reverse('todolist:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You dont have tasks for now.')
        self.assertQuerySetEqual(response.context['task_list'], [])

    def test_outdated_task(self):
        '''Testing if outdated task is displayed with Outdated mark'''
        task = create_task(task_name='Task', days=-5)
        response = self.c.get(reverse('todolist:index'))

        self.assertContains(response, 'Outdated')
        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_not_outdated_task(self):
        '''Testing if task with deadline in the future is displayed on index'''
        task = create_task(task_name='Task')
        response = self.c.get(reverse('todolist:index'))

        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_task_without_groups(self):
        '''Testing if an appropriate message displayed when task doesnt have groups'''
        task = create_task(task_name='Task')
        response = self.c.get(reverse('todolist:index'))

        self.assertContains(response, 'No groups')
        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_task_with_group(self):
        '''Testing if group name of the task is displayed'''
        group = create_group('TestGroup')
        task = create_task(task_name='Task', groups=[group])
        response = self.c.get(reverse('todolist:index'))

        self.assertContains(response, group.name)
        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_task_with_groups(self):
        '''Testing if names of groups of the task are displayed'''
        group1 = create_group('TestGroup 1')
        group2 = create_group('TestGroup 2')
        task = create_task(task_name='Task', groups=[group1, group2])
        response = self.c.get(reverse('todolist:index'))

        self.assertContains(response, f'{group1.name} - {group2.name}')
        self.assertQuerySetEqual(response.context['task_list'], [task])

class IndexTaskViewUserTests(TestCase):
    def setUp(self):
        self.c = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_task_visibility_to_unauthorized_user(self):
        '''Testing if task isnt displayed to unathorized user'''
        create_task(task_name='Task', user=self.user)
        response = self.c.get(reverse('todolist:index'))

        self.assertQuerySetEqual(response.context['task_list'], [])

    def test_task_visibility_to_logged_in_user(self):
        '''Testing if task is displayed to its owner'''
        self.c.login(username='testuser', password='12345')

        task = create_task(task_name='Task', user=self.user)
        response = self.c.get(reverse('todolist:index'))

        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_task_visibility_to_non_owner(self):
        '''Testing if task isnt displayed to non-owners'''
        self.owner = User.objects.create_user(username='owner_user', password='abcdeg')

        user = authenticate(username='testuser1', password='12345')
        self.c.login(user=user)

        create_task(task_name='Task', user=self.owner)
        response = self.c.get(reverse('todolist:index'))

        self.assertQuerySetEqual(response.context['task_list'], [])