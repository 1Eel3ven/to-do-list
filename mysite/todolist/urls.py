from django.urls import path

from . import views

app_name = 'todolist'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:task_id>/complete/', views.CompleteTask, name='complete_task'),
    path('create/', views.CreateTask, name='create_task'),
    path('addgroup/', views.AddGroup, name='add_group'),
]