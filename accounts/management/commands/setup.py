import os
import secrets
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection

class Command(BaseCommand):
    help = 'Initial secure setup of the application'

    def handle(self, *args, **options):
        self.stdout.write('Starting secure initial setup...')
        
        # Generate a secure secret key
        secret_key = secrets.token_urlsafe(50)
        
        # Update .env file with secure secret key
        env_file = os.path.join(os.getcwd(), '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                env_contents = f.read()
            
            if 'please-change-this-to-a-secure-random-secret-key' in env_contents:
                env_contents = env_contents.replace(
                    'please-change-this-to-a-secure-random-secret-key',
                    secret_key
                )
                with open(env_file, 'w') as f:
                    f.write(env_contents)
                self.stdout.write(self.style.SUCCESS('Generated and updated secure secret key'))
        
        # Run migrations
        self.stdout.write('Running database migrations...')
        call_command('migrate')
        
        # Create superuser if none exists
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('Creating superuser...')
            username = input('Enter superuser username: ')
            email = input('Enter superuser email: ')
            password = None
            while not password or len(password) < 12:
                password = input('Enter secure password (min 12 characters): ')
                if len(password) < 12:
                    self.stdout.write(self.style.ERROR('Password too short'))
            
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='ADMIN'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        
        # Create default groups and permissions
        self.stdout.write('Setting up default groups and permissions...')
        call_command('setup_groups')
        
        # Collect static files
        self.stdout.write('Collecting static files...')
        call_command('collectstatic', '--noinput')
        
        self.stdout.write(self.style.SUCCESS('Initial setup completed successfully'))
        self.stdout.write(
            '\nNext steps:'
            '\n1. Update the ALLOWED_HOSTS in .env with your domain'
            '\n2. Configure your email settings in .env'
            '\n3. Set up your database settings for production'
            '\n4. Configure SSL/TLS for production'
        )