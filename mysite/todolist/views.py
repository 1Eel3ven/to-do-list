from django.shortcuts import render
from django.http import HttpResponse

def TasksList(request):
    return HttpResponse('You`re on the list of tasks')

def TaskDetail(request):
    return HttpResponse('Detail of the task')
