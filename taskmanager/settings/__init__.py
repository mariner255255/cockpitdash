from .base import *

# Override settings based on environment
if os.environ.get('DJANGO_SETTINGS_MODULE') == 'taskmanager.settings.production':
    from .production import *
elif os.environ.get('DJANGO_SETTINGS_MODULE') == 'taskmanager.settings.development':
    from .development import *
else:
    # Default to development settings
    from .development import *
