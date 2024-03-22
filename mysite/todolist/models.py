from django.db import models
from django.utils import timezone

class TaskGroup(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Task(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)

    PRIORITYCHOICES = [
       ('Low', 'Low'),
       ('Medium', 'Medium'),
       ('High', 'High'),
       ('Critical', 'Critical'),
   ]
    
    priority = models.CharField(max_length=10, choices=PRIORITYCHOICES)

    creation_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()

    group = models.ManyToManyField(TaskGroup)

    def is_outdated(self):
        return self.deadline <= timezone.now()

    def __str__(self):
        return self.name
