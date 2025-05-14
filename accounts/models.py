from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import os

def validate_image_size(value):
    """Validate that uploaded image is under 5MB"""
    filesize = value.size
    if filesize > 5 * 1024 * 1024:  # 5MB limit
        raise ValidationError("Maximum file size is 5MB")

def profile_image_path(instance, filename):
    """Generate file path for profile images"""
    ext = filename.split('.')[-1]
    filename = f'{instance.username}_{timezone.now().strftime("%Y%m%d%H%M%S")}.{ext}'
    return os.path.join('profile_images', filename)

class PasswordHistory(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='password_history')
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Password histories'

class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    # Profile fields
    profile_picture = models.ImageField(
        upload_to=profile_image_path,
        validators=[validate_image_size],
        null=True,
        blank=True
    )

    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        MANAGER = 'MANAGER', _('Manager')
        USER = 'USER', _('User')
    
    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.USER,
    )
    
    # Profile fields
    profile_picture = models.ImageField(
        upload_to=profile_image_path,
        validators=[validate_image_size],
        null=True,
        blank=True
    )
    bio = models.TextField(max_length=500, blank=True)
    
    # Contact information
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    phone_regex = RegexValidator(
        regex=r'^\+44\d{10}$',
        message="Phone number must be entered in the format: '+441234567890'. Up to 11 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=13,
        blank=True,
        help_text="UK format: +441234567890"
    )
    
    # Account settings and security
    email_verified = models.BooleanField(default=False)
    account_locked = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    last_login_attempt = models.DateTimeField(null=True, blank=True)
    requires_password_change = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(auto_now_add=True)
    
    # User preferences
    display_name = models.CharField(max_length=30, blank=True)
    date_format = models.CharField(max_length=20, default="DD/MM/YYYY")
    timezone = models.CharField(max_length=50, default="UTC")
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        permissions = [
            ("can_view_dashboard", "Can view admin dashboard"),
            ("can_manage_users", "Can manage user accounts"),
            ("can_assign_tasks", "Can assign tasks to users"),
        ]
        
    def get_display_name(self):
        """Return the display name or username"""
        return self.display_name or self.username
        
    def lock_account(self):
        """Lock the account after too many failed attempts"""
        self.account_locked = True
        self.save()
        
    def reset_login_attempts(self):
        """Reset the failed login attempts counter"""
        self.failed_login_attempts = 0
        self.save()
        
    def increment_login_attempts(self):
        """Increment failed login attempts and lock if necessary"""
        self.failed_login_attempts += 1
        self.last_login_attempt = timezone.now()
        if self.failed_login_attempts >= 5:
            self.lock_account()
        self.save()
