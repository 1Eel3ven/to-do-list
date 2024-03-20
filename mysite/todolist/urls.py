from django.urls import path

from . import views

urlpatterns = [
    path('', views.TasksList, name='tasks_list'),
    path('detail/', views.TaskDetail, name='task_detail'),
]