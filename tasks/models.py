from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'TODO', _('To Do')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
    
    class Priority(models.TextChoices):
        LOW = 'LOW', _('Low')
        MEDIUM = 'MEDIUM', _('Medium')
        HIGH = 'HIGH', _('High')
    
    title = models.CharField(
        max_length=200,
        help_text=_('Task title')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Detailed description of the task')
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        help_text=_('Current status of the task')
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text=_('Task priority level')
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tasks',
        help_text=_('User who created the task')
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        help_text=_('User assigned to complete the task')
    )
    visible_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='visible_tasks',
        help_text=_('Users who can see this task'),
        blank=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text=_('User who owns this task')
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Date when the task is due')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the task was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When the task was last updated')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the task was completed')
    )
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("change_task_status", "Can change task status"),
            ("view_all_tasks", "Can view all tasks"),
            ("assign_task", "Can assign task to users"),
        ]
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['created_by', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    def clean(self):
        if self.due_date and self.due_date < timezone.now().date():
            raise ValidationError({
                'due_date': _('Due date cannot be in the past.')
            })
        
        if self.status == self.Status.COMPLETED and not self.assigned_to:
            raise ValidationError({
                'status': _('Cannot mark a task as completed without an assignee.')
            })
    
    def save(self, *args, **kwargs):
        from django.core.cache import cache
        
        is_new = self.pk is None
        
        if self.status == self.Status.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != self.Status.COMPLETED:
            self.completed_at = None
            
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Clear cache
        cache.delete(f'task_list_user_{self.created_by.id}')
        if not is_new:
            cache.delete(f'task_detail_{self.pk}')
            if self.assigned_to:
                cache.delete(f'task_list_user_{self.assigned_to.id}')
        
        # Ensure task is visible to creator and assignee
        if not self.visible_to.exists():
            self.visible_to.add(self.created_by)
            if self.assigned_to:
                self.visible_to.add(self.assigned_to)
    
    def can_view(self, user):
        """Check if user can view this task."""
        if user.is_superuser or user.has_perm('tasks.view_all_tasks'):
            return True
        return user in self.visible_to.all()
    
    def can_edit(self, user):
        """Check if user can edit this task."""
        if user.is_superuser:
            return True
        return user == self.created_by or user == self.assigned_to
    
    def can_delete(self, user):
        """Check if user can delete this task."""
        if user.is_superuser:
            return True
        return user == self.created_by
    
    def can_change_status(self, user):
        """Check if user can change task status."""
        if user.is_superuser or user.has_perm('tasks.change_task_status'):
            return True
        return user == self.assigned_to or user == self.created_by
    
    def get_status_color(self):
        """Get the Bootstrap color class for the status."""
        return {
            self.Status.TODO: 'secondary',
            self.Status.IN_PROGRESS: 'primary',
            self.Status.COMPLETED: 'success'
        }.get(self.status, 'secondary')
    
    def get_priority_color(self):
        """Get the Bootstrap color class for the priority."""
        return {
            self.Priority.LOW: 'info',
            self.Priority.MEDIUM: 'warning',
            self.Priority.HIGH: 'danger'
        }.get(self.priority, 'secondary')
