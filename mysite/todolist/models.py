from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone

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

    is_completed = models.BooleanField(default=False)
