from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.utils.translation import gettext as _
from django.utils import timezone
from accounts.models import PasswordHistory

class PasswordHistoryValidator:
    """
    Validate that the password hasn't been used in the recent password history.
    """
    
    def __init__(self, history_size=5):
        self.history_size = history_size

    def validate(self, password, user=None):
        if not user or user.pk is None:
            return
            
        # Check password history
        password_history = PasswordHistory.objects.filter(user=user)
        for history_entry in password_history:
            if check_password(password, history_entry.password):
                raise ValidationError(
                    _("This password has been used before. Please choose a different password."),
                    code='password_reused',
                )

    def password_changed(self, password, user=None):
        if not user or user.pk is None:
            return

        # Add the password to history
        PasswordHistory.objects.create(
            user=user,
            password=password,
            created_at=timezone.now()
        )
        
        # Remove old entries beyond history_size
        old_entries = PasswordHistory.objects.filter(user=user).order_by('-created_at')[self.history_size:]
        if old_entries.exists():
            PasswordHistory.objects.filter(pk__in=old_entries.values_list('pk', flat=True)).delete()

    def get_help_text(self):
        return _("Your password must not match any of your previous %d passwords.") % self.history_size
