from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import validate_email, RegexValidator
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class CustomAuthenticationForm(AuthenticationForm):
    """
    A form for authenticating users by email.
    """
    username = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    
    password = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        }),
    )
    
    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
        'locked': _("This account is locked due to too many failed attempts."),
    }

class CustomUserCreationForm(UserCreationForm):
    """
    A form for creating new users with email as the username.
    """
    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    
    password1 = forms.CharField(
        label=_('Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a strong password'
        }),
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{12,}$',
                message="Password must contain at least 12 characters, including letters, numbers, and special characters."
            ),
        ]
    )
    
    password2 = forms.CharField(
        label=_('Confirm Password'),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        }),
    )
    
    class Meta:
        model = CustomUser
        fields = ('email',)
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        validate_email(email)
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_('This email is already registered.'))
        return email
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email'].split('@')[0]
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    """
    A form for updating user profiles.
    """
    class Meta:
        model = CustomUser
        fields = ['profile_picture', 'bio', 'phone_number', 'display_name', 'timezone']
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tell us about yourself'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+441234567890'
            }),
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'How should we call you?'
            }),
            'timezone': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        
    def clean_profile_picture(self):
        image = self.cleaned_data.get('profile_picture')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError(_('Image file too large ( > 5MB )'))
            return image
        return None