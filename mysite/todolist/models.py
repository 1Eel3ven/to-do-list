from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

class BaseModel(models.Model):
    def save(self, *args, **kwargs):
        if self.pk is None and self.owner_id is None:
            self.owner = get_user_model().objects.first()
        super().save(*args, **kwargs)

    class Meta:
        abstract = True

class TaskGroup(BaseModel):
    name = models.CharField(max_length=50) 

    owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='taskgroups',
        default=None,
        null=True,
    )

    def __str__(self):
        return self.name

class Task(BaseModel):
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

    group = models.ManyToManyField(TaskGroup)

    owner = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='tasks',
        default=None,
        null=True,
    )

    def is_outdated(self):
        return self.deadline <= timezone.now()

    def __str__(self):
        return self.name