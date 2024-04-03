from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

PRIORITYCHOICES = [
       ('Low', 'Low'),
       ('Medium', 'Medium'),
       ('High', 'High'),
       ('Critical', 'Critical'),
   ]

class TaskGroup(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Task(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    
    priority = models.CharField(max_length=10, choices=PRIORITYCHOICES)

    creation_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()

    group = models.ManyToManyField(TaskGroup)

    def get_default_user_id():
        return get_user_model().objects.first().pk

    owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='tasks',
        default=get_default_user_id,
    )

    def is_outdated(self):
        return self.deadline <= timezone.now()

    def __str__(self):
        return self.name