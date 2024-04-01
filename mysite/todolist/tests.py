from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Task, TaskGroup

def create_task(task_name, days=5, groups=None):
    '''Creates a task that with deadline offset to now;
    Negative for task with deadline in the past; Positive for task with deadline in the future.'''
    time = timezone.now() + timedelta(days=days)
    task = Task.objects.create(name=task_name, deadline=time)

    if groups:
        for g in groups:
            task.group.add(g)

    return task

def create_group(group_name):
    group = TaskGroup.objects.create(name=group_name)

    return group

class QuestionTaskViewTests(TestCase):
    def test_no_tasks(self):
        '''Testing if an appropriate message displayed when no tasks exist'''
        response = self.client.get(reverse('todolist:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You dont have tasks for now.')
        self.assertQuerySetEqual(response.context['task_list'], [])

    def test_outdated_task(self):
        '''Testing if outdated task is displayed with Outdated mark'''
        task = create_task(task_name='Task', days=-5)
        response = self.client.get(reverse('todolist:index'))

        self.assertContains(response, 'Outdated')
        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_not_outdated_task(self):
        '''Testing if task with deadline in the future is displayed on index'''
        task = create_task(task_name='Task')
        response = self.client.get(reverse('todolist:index'))

        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_task_without_groups(self):
        '''Testing if an appropriate message displayed when task doesnt have groups'''
        task = create_task(task_name='Task')
        response = self.client.get(reverse('todolist:index'))

        self.assertContains(response, 'No groups')
        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_task_with_group(self):
        '''Testing if group name of the task is displayed'''
        group = create_group('TestGroup')
        task = create_task(task_name='Task', groups=[group])
        response = self.client.get(reverse('todolist:index'))

        self.assertContains(response, group.name)
        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_task_with_groups(self):
        '''Testing if names of groups of the task are displayed'''
        group1 = create_group('TestGroup 1')
        group2 = create_group('TestGroup 2')
        task = create_task(task_name='Task', groups=[group1, group2])
        response = self.client.get(reverse('todolist:index'))

        self.assertContains(response, f'{group1.name} - {group2.name}')
        self.assertQuerySetEqual(response.context['task_list'], [task])