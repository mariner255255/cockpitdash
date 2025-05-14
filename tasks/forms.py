from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'assigned_to', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get the user from kwargs
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
        
        # Set initial values for owner and created_by when creating a new task
        if not self.instance.pk and self.user:
            self.instance.owner = self.user
            self.instance.created_by = self.user
    
    def save(self, commit=True):
        if not self.user:
            raise ValueError("Task form requires a user.")
            
        instance = super().save(commit=False)
        if not instance.pk:  # Only set owner and created_by on new task creation
            instance.owner = self.user
            instance.created_by = self.user
            
        if commit:
            instance.save()
            self.save_m2m()
            # Ensure the task is visible to both creator and assignee
            instance.visible_to.add(self.user)
            if instance.assigned_to:
                instance.visible_to.add(instance.assigned_to)
        return instance
