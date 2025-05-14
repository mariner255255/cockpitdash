from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'created_by', 'assigned_to', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description')
        }),
        (_('Status'), {
            'fields': ('status', 'priority')
        }),
        (_('Assignment'), {
            'fields': ('created_by', 'assigned_to', 'visible_to')
        }),
        (_('Dates'), {
            'fields': ('due_date', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('visible_to',)
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
