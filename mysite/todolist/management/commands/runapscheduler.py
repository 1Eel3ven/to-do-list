import time

from django.conf import settings

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util

from todolist.models import CompletedTask


def clean_completed_tasks():
  """ 
  Cleans all the instances, since this model just stores info on completed tasks
  """

  print(CompletedTask.objects.all().delete())
    

@util.close_old_connections
def delete_old_job_executions(max_age=604_800):
    """
    This job deletes APScheduler job execution entries older than `max_age` from the database.
    It helps to prevent the database from filling up with old historical records that are no
    longer useful.
    """
  
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
  "Runs apscheduler"

  def handle(self, *args, **options):
    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
      clean_completed_tasks,
      trigger=CronTrigger(day="*/1"),  # Every day
      id="clean_completed_tasks",
      max_instances=1,
      replace_existing=True,
    )

    print("Added everyday job: 'clean_completed_tasks.")


    scheduler.add_job(
      delete_old_job_executions,
      trigger=CronTrigger(
        day_of_week="mon", hour="00", minute="00"
      ),  # Midnight on Monday, before start of the next work week.
      id="delete_old_job_executions",
      max_instances=1,
      replace_existing=True,
    )

    print("Added weekly job: 'delete_old_job_executions'.")

    scheduler.start()

    try:
      print('Scheduler started!')

      # This is here to simulate application activity (which keeps the main thread alive).
      while True:
        time.sleep(2)
    except KeyboardInterrupt:
      print('Stopping scheduler...')
      scheduler.shutdown()
      print('Scheduler shut down successfully!')

