from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from tasks.models import Task
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Create default groups and permissions for the application'

    def handle(self, *args, **options):
        self.stdout.write('Creating default groups and permissions...')
        
        # Create groups
        admin_group, _ = Group.objects.get_or_create(name='Administrators')
        manager_group, _ = Group.objects.get_or_create(name='Managers')
        user_group, _ = Group.objects.get_or_create(name='Users')
        
        # Get content types
        task_ct = ContentType.objects.get_for_model(Task)
        user_ct = ContentType.objects.get_for_model(CustomUser)
        
        # Create custom permissions
        view_dashboard = Permission.objects.get_or_create(
            codename='can_view_dashboard',
            name='Can view admin dashboard',
            content_type=user_ct,
        )[0]
        
        manage_users = Permission.objects.get_or_create(
            codename='can_manage_users',
            name='Can manage user accounts',
            content_type=user_ct,
        )[0]
        
        assign_tasks = Permission.objects.get_or_create(
            codename='can_assign_tasks',
            name='Can assign tasks to users',
            content_type=task_ct,
        )[0]
        
        # Get existing permissions
        view_task = Permission.objects.get(codename='view_task', content_type=task_ct)
        add_task = Permission.objects.get(codename='add_task', content_type=task_ct)
        change_task = Permission.objects.get(codename='change_task', content_type=task_ct)
        delete_task = Permission.objects.get(codename='delete_task', content_type=task_ct)
        
        # Assign permissions to groups
        # Administrators get all permissions
        admin_permissions = [
            view_dashboard, manage_users, assign_tasks,
            view_task, add_task, change_task, delete_task
        ]
        admin_group.permissions.set(admin_permissions)
        
        # Managers get task management permissions
        manager_permissions = [
            assign_tasks, view_task, add_task, change_task
        ]
        manager_group.permissions.set(manager_permissions)
        
        # Users get basic task permissions
        user_permissions = [
            view_task, add_task
        ]
        user_group.permissions.set(user_permissions)
        
        self.stdout.write(self.style.SUCCESS('Successfully created groups and assigned permissions'))
        
        # Assign existing users to groups based on their role
        users = CustomUser.objects.all()
        for user in users:
            if user.role == 'ADMIN':
                user.groups.add(admin_group)
            elif user.role == 'MANAGER':
                user.groups.add(manager_group)
            else:
                user.groups.add(user_group)
        
        self.stdout.write(self.style.SUCCESS('Successfully assigned users to groups'))