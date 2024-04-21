from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

class OwnerMixin(models.Model):
    def save(self, *args, **kwargs):
        # for running tests without specifying user when its not needed
        if self.pk is None and self.owner_id is None:
            self.owner = get_user_model().objects.first()
        super().save(*args, **kwargs)
    
    owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)ss",
        related_query_name="%(app_label)s_%(class)s",
        default=None,
        null=True,
    )

    class Meta:
        abstract = True

class TaskGroup(OwnerMixin):
    name = models.CharField(max_length=50) 

    def __str__(self):
        return self.name

class Task(OwnerMixin):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)

    PRIORITYCHOICES = [
       ('Low', 'Low'),
       ('Medium', 'Medium'),
       ('High', 'High'),
       ('Critical', 'Critical'),
   ]
    
    priority = models.CharField(max_length=10, choices=PRIORITYCHOICES)

    creation_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField()

    group = models.ManyToManyField(TaskGroup, blank=True)

    def is_outdated(self):
        return self.deadline <= timezone.now()

    def __str__(self):
        return self.name

class CompletedTask(OwnerMixin):
    '''Stores info about the task that is completed already'''

    name = models.CharField(max_length=50)
    complete_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name