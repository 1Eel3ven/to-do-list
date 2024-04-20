from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.utils import timezone
from django.forms.models import model_to_dict

from django.contrib.auth.models import User

from .models import Task, TaskGroup, CompletedTask

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

def create_completed_task(task_name, user=None):
    '''Creates a completed task instance in case you dont need to complete it manually'''
    user_id = user.id if user else None

    ctask = CompletedTask.objects.create(name=task_name, owner_id=user_id)

    return ctask

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
        self.assertContains(response, 'You dont have any tasks yet.')
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


class DeleteTaskViewTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def login_test_user(self):
        self.c.login(username=self.username, password=self.password)

    def test_404_for_unauthorized_user(self):
        '''Test if 404 is given when unauthorized user tries to access this view'''
        task = create_task(task_name='Task', user=self.user)

        response = self.c.post(reverse('todolist:delete_task', args=[task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_404_for_trying_to_delete_other_user_Task(self):
        '''Test if 404 is given when non-owner of the task tries to delete it'''
        self.owner = User.objects.create_user(username='owner_user', password='abcdeg')
        self.login_test_user()

        task = create_task(task_name='Task', user=self.owner)

        response = self.c.post(reverse('todolist:delete_task', args=[task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_task_delete(self):
        '''Test if delete works overall'''
        self.login_test_user()

        task = create_task(task_name='Task', user=self.user)

        # test if its initially displayed
        response = self.c.get(reverse('todolist:index'))
        self.assertQuerySetEqual(response.context['task_list'], [task])

        # delete
        response = self.c.post(reverse('todolist:delete_task', args=[task.pk]))
        self.assertNotEqual(response.status_code, 404)
        self.assertTrue(response.url.startswith(reverse('todolist:index')))

        # test if it dissapeared
        response = self.c.get(reverse('todolist:index'))
        self.assertQuerySetEqual(response.context['task_list'], [])


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


class EditTaskViewTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def login_test_user(self):
        self.c.login(username=self.username, password=self.password)

    def test_login_required_for_unauthorized_user(self):
        '''Testing if unauthorized user is redirected to login page when trying to access edit view'''
        task = create_task(task_name='Task', user=self.user)

        response = self.c.post(reverse('todolist:edit_task', args=[task.pk]))
        self.assertEqual(response.status_code, 302)

        # since redirect url contains next?=, startswith is used
        self.assertTrue(response.url.startswith(reverse('todolist:login')))

    def test_404_for_editing_nonexistent_task(self):
        '''Testing if 404 is given when user tries to access edit view for nonexistent task'''
        self.login_test_user()

        response = self.c.post(reverse('todolist:edit_task', args=[1]))
        self.assertEqual(response.status_code, 404)

    def test_404_for_editing_other_user_task(self):
        '''Testing if 404 is given when non-owner of the task tries to access edit view for the task'''
        self.login_test_user()
        self.owner = User.objects.create_user(username='owner_user', password='abcdeg')

        task = create_task(task_name='Task', user=self.owner)

        response = self.c.post(reverse('todolist:edit_task', args=[task.pk]))
        self.assertEqual(response.status_code, 404)

    def test_task_edit(self):
        '''Testing if editing of the task updates it successfully'''
        self.login_test_user()

        group1 = create_group('TestGroup 1', user=self.user)
        group2 = create_group('TestGroup 2', user=self.user)
        group3 = create_group('TestGroup 3', user=self.user)

        task = create_task(
            task_name='Task', 
            desc='Test task description', 
            days=5, 
            groups=[group1, group2], 
            user=self.user
            )

        updated_task_context = {
            'name': 'Updated task', 
            'description': 'Updated desc', 
            'priority': 'Critical', 
            'deadline': timezone.now(),
            'group': [group2.pk, group3.pk],
            # pk is for validation in the view
        }
        
        response = self.c.post(reverse('todolist:edit_task', args=[task.pk]), updated_task_context)

        # test if validation and redirect happened
        self.assertNotEqual(response.status_code, 404)
        self.assertEqual(response.url, reverse('todolist:index'))

        
        updated_task = Task.objects.get(pk=task.pk)
        updated_task_dict = model_to_dict(updated_task)
        updated_task_context['group'] = [group2, group3]

        # test if all fields were updated
        for field in updated_task_context.keys():
            self.assertEqual(updated_task_dict[field], updated_task_context[field])

        # test if updated task is on the index
        response = self.c.get(reverse('todolist:index'))
        self.assertQuerySetEqual(response.context['task_list'], [updated_task])


class CreateTaskViewTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def login_test_user(self):
        self.c.login(username=self.username, password=self.password)

    def test_login_required_for_unauthorized_user(self):
        '''Testing if unauthorized user is redirected to login page when trying to create a task'''

        response = self.c.post(reverse('todolist:add_group'), {})
        self.assertEqual(response.status_code, 302)

        self.assertTrue(response.url.startswith(reverse('todolist:login')))

    def test_task_create(self):
        '''Testing if task create works properly'''
        self.login_test_user()

        group1 = create_group('TestGroup 1', user=self.user)
        group2 = create_group('TestGroup 2', user=self.user)

        task_context = {
            'name': 'Test Task', 
            'description': 'Desc', 
            'priority': 'Medium', 
            'deadline': timezone.now(),
            'group': [group1.pk, group2.pk],
            # pk is for validation in the view
        }

        response = self.c.post(reverse('todolist:create_task'), task_context)

        # test if redirect happened
        self.assertEqual(response.url, reverse('todolist:index'))

        # since we dont know pk, get task by the deadline
        task = Task.objects.get(deadline=task_context['deadline'])
        task_dict = model_to_dict(task)
        task_context['group'] = [group1, group2]

        # test if all of the fields have the values they should
        for field in task_context.keys():
            self.assertEqual(task_dict[field], task_context[field])

        # test if index displays the created task
        response = self.c.get(reverse('todolist:index'))
        self.assertQuerySetEqual(response.context['task_list'], [task])

    def test_created_task_visibility(self):
        '''Test if created task is visible only to its owner'''
        self.owner = User.objects.create_user(username='owner', password='abcdeg')
        self.c.login(username='owner', password='abcdeg')

        task_context = {
            'name': 'Test Task', 
            'description': 'Desc', 
            'priority': 'Medium', 
            'deadline': timezone.now(),
            'group': [],
        }

        response = self.c.post(reverse('todolist:create_task'), task_context)

        # test if redirect happened
        self.assertEqual(response.url, reverse('todolist:index'))

        # since we dont know pk, get task by the deadline
        task = Task.objects.get(deadline=task_context['deadline'])

        # test if index displays the created task for the owner
        response = self.c.get(reverse('todolist:index'))
        self.assertQuerySetEqual(response.context['task_list'], [task])

        
        # log out the owner and login non-owner
        self.c.logout
        self.login_test_user()

        # test if created task isnt displayed to the non-owner
        response = self.c.get(reverse('todolist:index'))
        self.assertQuerySetEqual(response.context['task_list'], [])


class AddGroupViewTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login_required_for_unauthorized_user(self):
        '''Testing if unauthorized user is redirected to login page when trying to add a group'''

        response = self.c.post(reverse('todolist:add_group'), {'group_name': 'TestGroup'})
        self.assertEqual(response.status_code, 302)

        self.assertTrue(response.url.startswith(reverse('todolist:login')))

    def test_added_group_owner(self):
        '''Testing if the group after creation contains the user who added it as owner'''
        self.c.login(username=self.username, password=self.password)
        context = {'group_name': 'TestGroup'}

        response = self.c.post(reverse('todolist:add_group'), context)
        
        self.assertEqual(response.status_code, 302)
        # the views redirects user to the page where he`ve been, so just testing if its not login_required that happened
        self.assertFalse(response.url.startswith(reverse('todolist:login')))

        added_group = TaskGroup.objects.get(name=context['group_name'])
        self.assertTrue(added_group.owner, self.user)


class DeleteGroupViewTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login_required_for_unauthorized_user(self):
        '''Testing if unauthorized user is redirected to login page when trying to delete a group
        (unauthorized users cant see any groups, so this test made just in case)'''
        group = create_group(group_name='TestGroup')

        response = self.c.post(reverse('todolist:delete_group'), {'group': group.pk})
        self.assertEqual(response.status_code, 302)

        self.assertTrue(response.url.startswith(reverse('todolist:login')))

    def test_group_delete(self):
        '''Testing if group delete works properly'''
        self.c.login(username=self.username, password=self.password)

        group1 = create_group(group_name='TestGroup1', user=self.user)
        group2 = create_group(group_name='TestGroup2', user=self.user)

        response = self.c.post(reverse('todolist:delete_group'), {'group': [group1.pk, group2.pk]})

        self.assertEqual(response.status_code, 302)
        # the views redirects user to the page where he`ve been, so just testing if its not login_required that happened
        self.assertFalse(response.url.startswith(reverse('todolist:login')))

        self.assertQuerySetEqual(TaskGroup.objects.all(), [])


class RegisterViewTests(TestCase):
    def setUp(self):
        self.c = Client()

    def test_user_creation(self):
        '''Testing if register creates user properly'''
        context = {
            'username': 'JohnDoe', 
            'email': 'jdoe97@gmail.com', 
            'password1': '%qwerty123@', 
            'password2': '%qwerty123@',
        }

        response = self.c.post(reverse('todolist:register'), context)

        # test if user is redirected to the login after registering
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('todolist:login'))

        # test if User object was created
        self.assertNotEqual(User.objects.filter(email=context['email']), [])

    def test_error_message_display(self):
        '''Testing if error message is displayed on the page when validation of form fails'''
        context = {
                    'username': 'JohnDoe', 
                    'email': 'jdoe97@gmail.com', 
                    'password1': '123', 
                    'password2': '123',
                }
        
        response = self.c.post(reverse('todolist:register'), context)

        # test if user is redirected back to the register
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resolve(response.request['PATH_INFO']).url_name, 'register')

        self.assertIn('error_messages', response.content.decode('utf-8'))

class DashboardViewTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def login_test_user(self):
        self.c.login(username=self.username, password=self.password)

    def test_login_required_for_unauthorized_user(self):
        '''Testing if unauthorized user is redirected to login page when trying to access dashboard'''
        response = self.c.get(reverse('todolist:dashboard'))
        self.assertEqual(response.status_code, 302)

        self.assertTrue(response.url.startswith(reverse('todolist:login')))
    
    def test_empty_task_list_message(self):
        '''Testing if proper message is displayed in upcoming deadlines container if task list is empty'''
        self.login_test_user()

        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['task_list'], [])
        self.assertContains(response, 'You dont have any tasks yet.')

    def test_upcoming_deadline_tasks(self):
        '''Testing display of the tasks with upcoming deadline'''
        tasks = []
        self.login_test_user()

        # since only first 5 tasks with closest deadline are displayed, 
        # we`ll also checking that other wont be displayed
        for i in range(1, 7):
            task = create_task(task_name=f'Task {i}', days=i, user=self.user)
            tasks.append(task)

        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['task_list'], tasks[:5])

    def test_outdated_message(self):
        '''Testing if proper message is displayed if task is outdated already'''
        self.login_test_user()

        task = create_task(task_name='Task', days=-1, user=self.user)

        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['task_list'], [task])
        self.assertContains(response, 'Outdated')

    def test_completed_today_increment(self):
        '''Testing increment of completed tasks counter'''
        self.login_test_user()

        task = create_task(task_name='Task', user=self.user)
        
        response = self.c.get(reverse('todolist:dashboard'))

        # test if counter is 0 initially
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['completed_today'], 0)

        # increment
        response = self.c.post(reverse('todolist:complete_task', args=[task.pk]))
        self.assertNotEqual(response.status_code, 404)

        # test if increment counted
        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['completed_today'], 1)

    def test_completed_today_dicrease(self):
        '''Test if completed today counter dicreases after cleaning a ctask'''
        self.login_test_user()

        ctask = create_completed_task(task_name='Task', user=self.user)

        response = self.c.get(reverse('todolist:dashboard'))

        # test if initially counter is 1
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['completed_today'], 1)

        # dicrease
        response = self.c.get(reverse('todolist:clean_completed_task', args=[ctask.pk]))
        self.assertNotEqual(response.status_code, 404)

        # test if reduction counted
        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['completed_today'], 0)

    def test_completed_today_reset(self):
        '''Test if completed today counter resets after cleaning all ctasks'''
        self.login_test_user()

        for i in range(1, 7):
            ctask = create_completed_task(task_name=f'Task {i}', user=self.user)

        response = self.c.get(reverse('todolist:dashboard'))

        # test if initially counter equals quantity of ctasks
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['completed_today'], 6)

        # reset
        # type of request doesnt matter, though in the dashboard POST is used to delete all ctasks
        response = self.c.post(reverse('todolist:clean_completed_task'))
        self.assertNotEqual(response.status_code, 404)

        # test if counter is 0 indeed
        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['completed_today'], 0)

    def test_no_tasks_completed_recently_message(self):
        '''Testing if proper message is displayed in completed recently tasks container if user havent completed any tasks'''
        self.login_test_user()

        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['completed_recently'], [])
        self.assertContains(response, 'You havent completed any tasks recently.')

    def test_completed_recently(self):
        '''Testing display of recently completed tasks'''
        tasks = []
        self.login_test_user()

        # since only first 4 recently completed tasks by complete time are displayed, 
        # we`ll also checking that other wont be displayed
        for i in range(1, 6):
            task = create_task(task_name=f'Task {i}', days=i, user=self.user)
            tasks.append(task)

        # test if recent tasks are empty initially
        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['completed_recently'], [])

        # complete tasks
        for i in range(len(tasks)):
            task = tasks[i]

            request = self.c.post(reverse('todolist:complete_task', args=[task.pk]))
            self.assertNotEqual(request.status_code, 404)

            # for further comparison with the queryset
            tasks[i] = CompletedTask.objects.get(name=task.name)

        # test if recently completed tasks are displayed
        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['completed_recently'], tasks[:4])

    def test_completed_recently_when_clean_ctask(self):
        '''Testing if cleaned ctask dissapears from recently completed tasks'''
        self.login_test_user()

        ctask = create_completed_task(task_name='Task', user=self.user)

        # test if recent tasks contain ctask initially
        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['completed_recently'], [ctask])

        # type of request doesnt matter, though in the dashboard GET is used to delete particular ctask
        response = self.c.get(reverse('todolist:clean_completed_task', args=[ctask.pk]))

        # test if ctask dissapeared from recently completed
        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['completed_recently'], [])

    def test_completed_recently_when_clean_all_ctasks(self):
        '''Testing if after cleaning all of ctasks they dissapear from recently completed tasks'''
        ctasks = []
        self.login_test_user()

        for i in range(1, 5):
            ctask = create_completed_task(task_name=f'Task {i}', user=self.user)
            ctasks.append(ctask)

        # test if recent tasks contain ctasks initially
        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['completed_recently'], ctasks)

        # clean all ctasks
        response = self.c.post(reverse('todolist:clean_completed_task'))

        # test if ctasks dissapeared from recently completed
        response = self.c.get(reverse('todolist:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['completed_recently'], [])


class CleanCompletedTaskViewTests(TestCase):
    def setUp(self):
        self.c = Client()
        
        self.username = 'test_user'
        self.password = '12345'
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def login_test_user(self):
        self.c.login(username=self.username, password=self.password)

    def test_login_required(self):
        '''Testing if unauthorized user is redirected to login page when trying to access the view'''

        response = self.c.get(reverse('todolist:clean_completed_task'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('todolist:login')))

    def test_clean_ctask(self):
        '''Testing if cleaning of the completed task with given id works'''
        self.login_test_user()
        
        ctask = create_completed_task(task_name='Task', user=self.user)

        # type of request doesnt matter, though in the dashboard GET is used to delete particular ctask
        response = self.c.get(reverse('todolist:clean_completed_task', args=[ctask.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('todolist:dashboard')))
        self.assertQuerySetEqual(CompletedTask.objects.all(), [])

    def test_404_for_cleaning_nonexistent_ctask(self):
        self.login_test_user()

        response = self.c.get(reverse('todolist:clean_completed_task', args=[1]))

        self.assertEqual(response.status_code, 404)

    def test_clean_all_ctasks(self):
        '''Testing if all of user`s completed tasks are cleaned if no id provided to the view'''
        ctasks = []
        self.login_test_user()
        
        for i in range(1, 6):
            ctask = create_completed_task(task_name=f'Task {i}', user=self.user)
            ctasks.append(ctask)

        # check all ctasks are initially here
        self.assertQuerySetEqual(list(CompletedTask.objects.all()), ctasks)

        # type of request doesnt matter, though in the dashboard POST is used to delete all ctasks
        response = self.c.get(reverse('todolist:clean_completed_task'))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('todolist:dashboard')))
        self.assertQuerySetEqual(CompletedTask.objects.all(), [])




