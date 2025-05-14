from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import UpdateView
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.translation import gettext as _
from django.core.cache import cache
from datetime import timedelta
from .forms import CustomAuthenticationForm as SecureAuthenticationForm, CustomUserCreationForm as SecureUserCreationForm
from .models import CustomUser

def get_client_ip(request):
    """
    Get the client's IP address from the request, handling proxy servers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Get the first IP in the chain (original client IP)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_ratelimit(request):
    """
    Check if the request should be rate limited.
    Returns (is_limited, attempts_remaining, lockout_minutes)
    """
    ip = get_client_ip(request)
    cache_key = f'rl:{ip}'
    attempts = cache.get(cache_key, 0)
    
    if attempts >= 5:  # Max attempts
        last_attempt = cache.get(f'{cache_key}:timestamp')
        if last_attempt:
            now = timezone.now()
            lockout_until = last_attempt + timedelta(minutes=30)
            if now < lockout_until:
                minutes_remaining = int((lockout_until - now).total_seconds() / 60)
                return True, 0, minutes_remaining
    
    remaining = 5 - attempts
    return False, remaining, 0

def ratelimit_view(request, exception):
    """
    View to handle rate-limited requests.
    """
    is_limited, attempts_remaining, lockout_minutes = check_ratelimit(request)
    if is_limited:
        return HttpResponseForbidden(
            _('Too many login attempts. Please try again in {} minutes.').format(lockout_minutes)
        )
    return HttpResponseForbidden(_('Rate limit exceeded. Please try again later.'))

def custom_permission_denied(request, exception=None):
    """Custom 403 error handler."""
    return render(request, 'errors/error.html', {
        'error_code': 403,
        'error_message': 'Permission denied. You do not have access to this resource.',
    }, status=403)

def custom_page_not_found(request, exception=None):
    """Custom 404 error handler."""
    return render(request, 'errors/error.html', {
        'error_code': 404,
        'error_message': 'The requested page could not be found.',
    }, status=404)

def custom_server_error(request):
    """Custom 500 error handler."""
    return render(request, 'errors/error.html', {
        'error_code': 500,
        'error_message': 'An internal server error occurred. Please try again later.',
    }, status=500)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    # Check rate limiting
    is_limited, attempts_remaining, lockout_minutes = check_ratelimit(request)
    if is_limited:
        messages.error(request, 
            _('Too many login attempts. Please try again in {} minutes.').format(lockout_minutes))
        return render(request, 'accounts/lockout.html')
        
    if request.method == 'POST':
        form = SecureAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Reset rate limiting on successful login
            ip = get_client_ip(request)
            cache.delete(f'rl:{ip}')
            cache.delete(f'rl:{ip}:timestamp')
            
            # Reset user's failed login attempts
            user.failed_login_attempts = 0
            user.last_login_attempt = timezone.now()
            user.save()
            
            # Log the user in
            login(request, user)
            
            # Check if password change is required
            if user.requires_password_change:
                messages.warning(request, _('Please change your password to continue.'))
                return redirect('password_change')
                
            return redirect('home')
        else:
            # Increment rate limiting counter
            ip = get_client_ip(request)
            cache_key = f'rl:{ip}'
            attempts = cache.get(cache_key, 0)
            cache.set(cache_key, attempts + 1, 300)  # 5 minutes timeout
            cache.set(f'{cache_key}:timestamp', timezone.now(), 1800)  # 30 minutes timeout
            
            # Update user's failed login attempts if account exists
            username = request.POST.get('username')
            try:
                user = CustomUser.objects.get(username=username)
                user.increment_login_attempts()
                user.last_login_attempt = timezone.now()
                user.save()
            except CustomUser.DoesNotExist:
                pass
                
            if attempts_remaining > 0:
                messages.error(request, 
                    _('Invalid login. {} attempts remaining.').format(attempts_remaining))
    else:
        form = SecureAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = SecureUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.last_login_attempt = timezone.now()
            user.save()
            login(request, user)
            return redirect('home')
    else:
        form = SecureUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    fields = ['email', 'phone_number']
    template_name = 'accounts/update_profile.html'
    success_url = reverse_lazy('profile')
    
    def test_func(self):
        return self.request.user.id == self.get_object().id

@login_required
def change_password_view(request):
    if request.method == 'POST':
        user = request.user
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('change_password')
            
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return redirect('change_password')
            
        user.set_password(new_password)
        user.last_password_change = timezone.now()
        user.requires_password_change = False
        user.save()
        login(request, user)
        messages.success(request, 'Password changed successfully.')
        return redirect('profile')
        
    return render(request, 'accounts/change_password.html')
