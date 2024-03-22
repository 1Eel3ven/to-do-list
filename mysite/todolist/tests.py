from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Task

def create_task(task_name, days):
    '''Creates a task that with deadline offset to now;
    Negative for task with deadline in the past; Positive for task with deadline in the future.'''
    time = timezone.now() + timedelta(days=days)
    task = Task.objects.create(name=task_name, deadline=time)

    return task

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
        task = create_task(task_name='Task', days=5)
        response = self.client.get(reverse('todolist:index'))

        self.assertQuerySetEqual(response.context['task_list'], [task])