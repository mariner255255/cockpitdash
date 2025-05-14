from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def check_task_deadlines():
    """
    Check for upcoming task deadlines and send notifications
    """
    from .models import Task
    
    # Tasks due in the next 24 hours
    upcoming_tasks = Task.objects.filter(
        due_date__range=(
            timezone.now(),
            timezone.now() + timedelta(days=1)
        ),
        completed=False
    )
    
    for task in upcoming_tasks:
        send_task_reminder.delay(task.id)

@shared_task
def send_task_reminder(task_id):
    """
    Send reminder email for a task
    """
    from .models import Task
    
    try:
        task = Task.objects.get(id=task_id)
        subject = f'Task Reminder: {task.title}'
        message = render_to_string('tasks/email/reminder.html', {
            'task': task
        })
        
        # Send to task owner and all assignees
        recipients = [task.owner.email]
        recipients.extend(task.assignees.values_list('email', flat=True))
        
        send_mail(
            subject,
            message,
            None,  # Use DEFAULT_FROM_EMAIL
            recipients,
            html_message=message
        )
        
    except Task.DoesNotExist:
        logger.error(f'Task {task_id} not found')
    except Exception as e:
        logger.error(f'Error sending reminder for task {task_id}: {str(e)}')

@shared_task
def send_daily_digest():
    """
    Send daily digest of tasks to users
    """
    for user in User.objects.filter(is_active=True):
        from .models import Task
        
        # Get user's tasks
        tasks = Task.objects.filter(
            owner=user,
            completed=False
        ).order_by('due_date')
        
        if tasks:
            subject = 'Your Daily Task Digest'
            message = render_to_string('tasks/email/daily_digest.html', {
                'user': user,
                'tasks': tasks
            })
            
            send_mail(
                subject,
                message,
                None,
                [user.email],
                html_message=message
            )

@shared_task
def process_task_changes(task_id, action, user_id):
    """
    Process task changes and notify relevant users
    """
    from .models import Task, TaskActivity
    
    try:
        task = Task.objects.get(id=task_id)
        user = User.objects.get(id=user_id)
        
        # Record activity
        TaskActivity.objects.create(
            task=task,
            user=user,
            action=action
        )
        
        # Notify relevant users
        notify_users.delay(task_id, action, user_id)
        
    except (Task.DoesNotExist, User.DoesNotExist):
        logger.error(f'Task {task_id} or User {user_id} not found')

@shared_task
def notify_users(task_id, action, actor_id):
    """
    Notify users about task changes
    """
    from .models import Task, Notification
    
    try:
        task = Task.objects.get(id=task_id)
        actor = User.objects.get(id=actor_id)
        
        # Determine recipients (owner, assignees, watchers)
        recipients = set()
        recipients.add(task.owner)
        recipients.update(task.assignees.all())
        recipients.update(task.watchers.all())
        
        # Remove actor from recipients
        recipients.discard(actor)
        
        # Create notifications
        for recipient in recipients:
            Notification.objects.create(
                user=recipient,
                task=task,
                action=action,
                actor=actor
            )
            
    except (Task.DoesNotExist, User.DoesNotExist):
        logger.error(f'Task {task_id} or User {actor_id} not found')

@shared_task
def sync_external_tasks():
    """
    Sync tasks with external systems (placeholder for integration)
    """
    # Implement integration with external systems here
    pass

@shared_task
def cleanup_old_notifications():
    """
    Clean up old notifications
    """
    from .models import Notification
    
    # Delete notifications older than 30 days
    cutoff_date = timezone.now() - timedelta(days=30)
    Notification.objects.filter(created_at__lt=cutoff_date).delete()

@shared_task
def update_task_analytics():
    """
    Update task analytics for dashboards
    """
    from .models import Task, TaskAnalytics
    
    # Calculate various metrics
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(completed=True).count()
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now(),
        completed=False
    ).count()
    
    # Update analytics
    TaskAnalytics.objects.create(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        completion_rate=completed_tasks/total_tasks if total_tasks > 0 else 0
    )
