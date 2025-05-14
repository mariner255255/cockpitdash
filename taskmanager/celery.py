import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskmanager.settings.development')

# Create Celery app
app = Celery('taskmanager')

# Config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'check-task-deadlines': {
        'task': 'tasks.tasks.check_task_deadlines',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'send-daily-digest': {
        'task': 'tasks.tasks.send_daily_digest',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    'sync-external-tasks': {
        'task': 'tasks.tasks.sync_external_tasks',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'cleanup-old-notifications': {
        'task': 'tasks.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
}

# Task routing
app.conf.task_routes = {
    'tasks.tasks.send_notification': {'queue': 'notifications'},
    'tasks.tasks.process_task_changes': {'queue': 'changes'},
    'tasks.tasks.sync_external_tasks': {'queue': 'sync'},
    'tasks.tasks.*': {'queue': 'default'},
}

# Task settings
app.conf.task_time_limit = 30 * 60  # 30 minutes
app.conf.task_soft_time_limit = 25 * 60  # 25 minutes
