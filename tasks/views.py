from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.translation import gettext as _
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.utils.cache import patch_response_headers
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Task
from .forms import TaskForm
import logging

logger = logging.getLogger(__name__)

CACHE_TTL = 60 * 5  # Cache for 5 minutes

@require_http_methods(["GET"])
def cache_test(request):
    """
    Test view to verify Redis cache functionality.
    Try to get the value from cache, if not found, set it and return.
    """
    cache_key = 'cache_test_key'
    cache_value = cache.get(cache_key)
    
    if cache_value is None:
        cache_value = 'Cache is working!'
        cache.set(cache_key, cache_value, timeout=300)  # 5 minutes timeout
        was_cached = False
    else:
        was_cached = True
    
    return JsonResponse({
        'value': cache_value,
        'was_cached': was_cached
    })

@login_required
def task_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    page = request.GET.get('page', '1')
    
    # Create a unique cache key based on all filters
    cache_key = f'task_list_user_{request.user.id}_q_{query}_s_{status_filter}_p_{priority_filter}_page_{page}'
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        logger.debug('Task list cache miss')
        tasks = Task.objects.filter(created_by=request.user)
        
        if query:
            tasks = tasks.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
        
        if status_filter:
            tasks = tasks.filter(status=status_filter)
            
        if priority_filter:
            tasks = tasks.filter(priority=priority_filter)
            
        tasks = tasks.order_by('-created_at')
        
        paginator = Paginator(tasks, 10)
        tasks_page = paginator.get_page(page)
        
        # Cache both the QuerySet and pagination data
        cached_data = {
            'tasks': list(tasks_page.object_list),
            'has_previous': tasks_page.has_previous(),
            'has_next': tasks_page.has_next(),
            'number': tasks_page.number,
            'num_pages': tasks_page.paginator.num_pages
        }
        cache.set(cache_key, cached_data, CACHE_TTL)
    else:
        logger.debug('Task list cache hit')
    
    # Get choices for filters
    status_choices = Task.Status.choices
    priority_choices = Task.Priority.choices
    
    context = {
        'tasks': cached_data['tasks'],
        'page_obj': {
            'has_previous': cached_data['has_previous'],
            'has_next': cached_data['has_next'],
            'number': cached_data['number'],
            'num_pages': cached_data['num_pages']
        },
        'status_choices': status_choices,
        'priority_choices': priority_choices,
        'current_page': 'tasks',
        'query': query,
        'status_filter': status_filter,
        'priority_filter': priority_filter
    }
    
    response = render(request, 'tasks/task_list.html', context)
    patch_response_headers(response, CACHE_TTL)
    return response

@login_required
def task_detail(request, pk):
    # Create a cache key specific to this user and task
    cache_key = f'task_detail_{pk}_user_{request.user.id}'
    cached_task = cache.get(cache_key)
    
    if cached_task is None:
        logger.debug('Task detail cache miss')
        # First check if the user can view this task
        task = get_object_or_404(Task, pk=pk)
        if not task.can_view(request.user):
            return HttpResponseForbidden(_("You don't have permission to view this task."))
            
        cache.set(cache_key, task, CACHE_TTL)
        cached_task = task
    else:
        logger.debug('Task detail cache hit')
    
    context = {
        'task': cached_task,
        'current_page': 'tasks'
    }
    
    response = render(request, 'tasks/task_detail.html', context)
    patch_response_headers(response, CACHE_TTL)
    return response

@login_required
def task_new(request):
    if request.method == "POST":
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                task = form.save()
                # Cache invalidation is handled in the model's save method
                messages.success(request, 'Task was created successfully.')
                return redirect('tasks:task_list')
            except Exception as e:
                logger.error(f"Error creating task: {str(e)}")
                messages.error(request, 'Error creating task. Please try again.')
                return redirect('tasks:task_create')
    else:
        form = TaskForm(user=request.user, initial={
            'status': 'TODO',  # Set default status
            'priority': 'MEDIUM',  # Set default priority
        })
    return render(request, 'tasks/task_form.html', {'form': form, 'current_page': 'tasks'})

@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, created_by=request.user)
    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            
            # Invalidate both list and detail cache
            cache.delete(f'task_list_user_{request.user.id}')
            cache.delete(f'task_detail_{pk}')
            
            messages.success(request, 'Task was updated successfully.')
            return redirect('tasks:task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'current_page': 'tasks'})

@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, created_by=request.user)
    if request.method == "POST":
        task.delete()
        
        # Invalidate both list and detail cache
        cache.delete(f'task_list_user_{request.user.id}')
        cache.delete(f'task_detail_{pk}')
        
        messages.success(request, 'Task was deleted successfully.')
        return redirect('tasks:task_list')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task, 'current_page': 'tasks'})

@login_required
def task_complete(request, pk):
    task = get_object_or_404(Task, pk=pk, created_by=request.user)
    task.status = 'DONE'
    task.completed_at = timezone.now()
    task.save()
    
    # Invalidate both list and detail cache
    cache.delete(f'task_list_user_{request.user.id}')
    cache.delete(f'task_detail_{pk}')
    
    messages.success(request, 'Task was marked as complete.')
    return redirect('tasks:task_list')
