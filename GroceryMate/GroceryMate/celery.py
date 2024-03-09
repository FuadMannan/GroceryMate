import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'GroceryMate.settings')

app = Celery('GroceryMate')

# Set timezone
app.conf.enable_utc = False
app.conf.update(timezone='America/Toronto')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Set Celery Beat settings
app.conf.beat_schedule = {
    'nightly-scrape': {
        'task': 'myapp.tasks.scrape_task',
        'schedule': crontab(hour=0, minute=30)
    }
}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')