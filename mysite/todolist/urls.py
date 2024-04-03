from django.urls import path

from . import views

app_name = 'todolist'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.EditView.as_view(), name='edit'),
    path('<int:task_id>/complete/', views.CompleteTask, name='complete_task'),
    path('create/', views.CreateTask, name='create_task'),
    path('<int:task_id>/edit_task/', views.EditTask, name='edit_task'),
    path('addgroup/', views.AddGroup, name='add_group'),
    path('deletegroup/', views.DeleteGroup, name='delete_group'),
    path('login/', views.LoginView, name='login'),
    path('register/', views.RegisterView, name='register'),
    path('logout/', views.LogOutView, name='logout')
]