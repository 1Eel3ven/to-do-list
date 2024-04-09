from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.forms.models import model_to_dict

from django.contrib.auth.models import User

from .models import Task, TaskGroup
from .forms import TaskForm

def create_task(task_name, desc='desc', pr='Medium', days=5, groups=None, user=None):
    '''Creates a task with deadline offset to now;
    Negative for task with deadline in the past; Positive for task with deadline in the future.'''
    time = timezone.now() + timedelta(days=days)
    user_id = user.id if user else None

    task = Task.objects.create(
        name=task_name, 
        description=desc, 
        priority=pr, 
        deadline=time, 
        owner_id=user_id
        )

    if groups:
        for g in groups:
            task.group.add(g)

    return task

def create_group(group_name, user=None):
    user_id = user.id if user else None

    group = TaskGroup.objects.create(name=group_name, owner_id=user_id)

    return group


# index page tests where user isnt required
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


# index page tests with user
class IndexTaskViewUserTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_task_visibility_to_unauthorized_user(self):
        '''Testing if task isnt displayed to unathorized user'''
        create_task(task_name='Task', user=self.user)
        response = self.c.get(reverse('todolist:index'))

        self.assertQuerySetEqual(response.context['task_list'], [])

    def test_task_visibility_to_logged_in_user(self):
        '''Testing if task is displayed to its owner'''
        self.c.login(username=self.username, password=self.password)

        task = create_task(task_name='Task', user=self.user)
        response = self.c.get(reverse('todolist:index'))

        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_task_visibility_to_non_owner(self):
        '''Testing if task isnt displayed to non-owners'''
        self.owner = User.objects.create_user(username='owner_user', password='abcdeg')

        self.c.login(username=self.username, password=self.password)

        create_task(task_name='Task', user=self.owner)
        response = self.c.get(reverse('todolist:index'))

        self.assertQuerySetEqual(response.context['task_list'], [])


class DetailViewTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def login_test_user(self):
        self.c.login(username=self.username, password=self.password)

    def test_group_display(self):
        '''Testing if group of the task is displayed'''
        self.login_test_user()

        group = create_group('TestGroup', user=self.user)
        task = create_task(task_name='Task', groups=[group], user=self.user)

        response = self.c.get(reverse('todolist:detail', args=[task.pk]))

        self.assertContains(response, group.name)

    def test_groups_display(self):
        '''Testing if groups of the task are displayed'''
        self.login_test_user()

        group1 = create_group('TestGroup 1', user=self.user)
        group2 = create_group('TestGroup 2', user=self.user)
        task = create_task(task_name='Task', groups=[group1, group2], user=self.user)

        response = self.c.get(reverse('todolist:detail', args=[task.pk]))

        self.assertContains(response, f'{group1.name} - {group2.name}')

    def test_404_for_nonexistent_task(self):
        '''Testing if trying to access nonexistent task gives 404'''
        response = self.c.get(reverse('todolist:detail', args=[1]))

        self.assertEqual(response.status_code, 404)

    def test_404_for_unauthorized_user(self):
        '''Testing if 404 is given when unauthorized user tries to access some task`s detail page'''
        task = create_task(task_name='Task', user=self.user)
        response = self.c.get(reverse('todolist:detail', args=[task.pk]))

        self.assertEqual(response.status_code, 404)

    def test_page_for_task_owner(self):
        '''Testing if task owner can successfully access the detail page of his task'''
        self.login_test_user()

        task = create_task(task_name='Task', user=self.user)
        response = self.c.get(reverse('todolist:detail', args=[task.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, task.name)

    def test_404_for_non_task_owner(self):
        '''Testing if 404 is given when user tries to access some task`s detail page of other user'''
        self.owner = User.objects.create_user(username='owner_user', password='abcdeg')
        self.login_test_user()

        task = create_task(task_name='Task', user=self.owner)
        response = self.c.get(reverse('todolist:detail', args=[task.pk]))

        self.assertEqual(response.status_code, 404)


class CompleteTaskViewTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_task_complete_on_index(self):
        '''Testing if task dissapears from the index page when user clicks on complete checkbox'''
        self.c.login(username=self.username, password=self.password)
        task = create_task(task_name='Task', user=self.user)

        response = self.c.get(reverse('todolist:index'))
        self.assertQuerySetEqual(response.context['task_list'], [task])

        self.c.post(reverse('todolist:complete_task', args=[task.pk]))

        response = self.c.get(reverse('todolist:index'))
        self.assertQuerySetEqual(response.context['task_list'], [])

    def test_404_for_trying_to_complete_nonexistent_task(self):
        '''Testing if 404 is given when completing of the nonexistent task is attempted'''
        response = self.c.post(reverse('todolist:complete_task', args=[1]))
        self.assertEqual(response.status_code, 404)

    def test_404_for_trying_to_complete_other_user_task(self):
        '''Testing if 404 is given if user uses tries to access CompleteTask view to complete other user`s task'''
        self.owner = User.objects.create_user(username='owner_user', password='abcdeg')
        self.c.login(username=self.username, password=self.password)

        task = create_task(task_name='Task', user=self.owner)

        response = self.c.post(reverse('todolist:complete_task', args=[task.pk]))
        self.assertEqual(response.status_code, 404)


class EditPageTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def login_test_user(self):
        self.c.login(username=self.username, password=self.password)

    def test_404_for_accessing_edit_page_of_nonexistent_task(self):
        '''Testing if 404 is given when user tries to access edit page of nonexistent task'''
        self.login_test_user()

        task = create_task(task_name='Task', user=self.user)

        response = self.c.get(reverse('todolist:edit', args=[task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_404_for_accessing_edit_page_of_nonexistent_task(self):
        '''Testing if 404 is given when non-owner of task tries to access edit page of the task'''
        self.owner = User.objects.create_user(username='owner_user', password='abcdeg')
        self.login_test_user()

        task = create_task(task_name='Task', user=self.owner)

        response = self.c.get(reverse('todolist:edit', args=[task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_task_form_data_equals_to_task_data(self):
        '''Testing if task form data is simillar to the task user is going to edit'''
        self.login_test_user()
        
        group1 = create_group('TestGroup 1', user=self.user)
        group2 = create_group('TestGroup 2', user=self.user)

        task = create_task(
            task_name='Task', 
            desc='Test task description', 
            days=5, 
            groups=[group1, group2], 
            user=self.user
            )

        response = self.c.get(reverse('todolist:edit', args=[task.pk]))

        task_form = response.context['task_form'].initial
        task_dict = model_to_dict(task)

        for field in ['name', 'description', 'priority', 'deadline', 'group']:
            self.assertEqual(task_form[field], task_dict[field])


