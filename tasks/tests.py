from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from .models import Task

class TaskTests(TestCase):
    def setUp(self):
        # Clear the cache before each test
        cache.clear()
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.due_date = timezone.now() + timedelta(days=7)
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            created_by=self.user,
            owner=self.user,  # Set the owner field
            priority='HIGH',
            status='TODO',
            due_date=self.due_date
        )

    def test_task_creation(self):
        """Test task creation"""
        task = Task.objects.get(id=1)
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.created_by, self.user)
        self.assertEqual(task.owner, self.user)
          def test_task_list_view(self):
        """Test task list view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tasks:task_list'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')
    
    def test_task_detail_view(self):
        """Test task detail view"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('tasks:task_detail', args=[self.task.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')
        
    def test_create_task_view(self):
        """Test task creation view"""
        self.client.login(username='testuser', password='testpass123')
        data = {
            'title': 'New Task',
            'description': 'New Description',
            'priority': 'MEDIUM',
            'status': 'TODO',
            'due_date': self.due_date.strftime('%Y-%m-%d'),  # Match the DateInput widget format
            'assigned_to': self.user.id  # Assign to the test user
        }
        response = self.client.post(reverse('tasks:task_create'), data, follow=True)
        self.assertEqual(response.status_code, 200)  # Check if the request was successful
        self.assertEqual(Task.objects.count(), 2)  # Verify there are 2 tasks
        new_task = Task.objects.get(title='New Task')
        self.assertEqual(new_task.created_by, self.user)
        self.assertEqual(new_task.owner, self.user)
        self.assertEqual(new_task.assigned_to, self.user)  # Verify assignee

    def test_task_list_cache(self):
        """Test that task list is properly cached"""
        self.client.login(username='testuser', password='testpass123')
        cache_key = f'task_list_user_{self.user.id}'
        
        # First request - should hit the database
        response1 = self.client.get(reverse('tasks:task_list'), follow=True)
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, 'Test Task')
        
        # Create a new task
        Task.objects.create(
            title='Another Task',
            description='Another Description',
            created_by=self.user,
            owner=self.user,
            priority='LOW',
            status='TODO',
            due_date=self.due_date
        )
        
        # Second request - should still get cached data
        response2 = self.client.get(reverse('tasks:task_list'), follow=True)
        self.assertEqual(response2.status_code, 200)
        self.assertNotContains(response2, 'Another Task')  # New task shouldn't appear due to cache

    def test_task_detail_cache(self):
        """Test that task detail is properly cached"""
        self.client.login(username='testuser', password='testpass123')
        cache_key = f'task_detail_{self.task.id}'
        
        # First request - should hit the database
        response1 = self.client.get(reverse('tasks:task_detail', args=[self.task.id]), follow=True)
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, 'Test Task')
        
        # Update the task
        self.task.title = 'Updated Task Title'
        self.task.save()
        
        # Second request - should still get cached data
        response2 = self.client.get(reverse('tasks:task_detail', args=[self.task.id]), follow=True)
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, 'Test Task')  # Should show old title due to cache
        self.assertNotContains(response2, 'Updated Task Title')  # New title shouldn't appear due to cache

    def test_task_list_cache_with_filters(self):
        """Test that task list caching works with filters"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test with status filter
        response1 = self.client.get(reverse('tasks:task_list') + '?status=TODO', follow=True)
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, 'Test Task')
        
        # Create a completed task
        Task.objects.create(
            title='Completed Task',
            description='A completed task',
            created_by=self.user,
            owner=self.user,
            status='COMPLETED',
            priority='LOW',
            due_date=self.due_date
        )
        
        # Second request with same filter - should still get cached data
        response2 = self.client.get(reverse('tasks:task_list') + '?status=TODO', follow=True)
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, 'Test Task')
        self.assertNotContains(response2, 'Completed Task')
        
        # Different filter should bypass cache
        response3 = self.client.get(reverse('tasks:task_list') + '?status=COMPLETED', follow=True)
        self.assertEqual(response3.status_code, 200)
        self.assertContains(response3, 'Completed Task')

    def test_task_list_cache_invalidation(self):
        """Test that task list cache is properly invalidated"""
        self.client.login(username='testuser', password='testpass123')
        
        # Initial request
        response1 = self.client.get(reverse('tasks:task_list'), follow=True)
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, 'Test Task')
        
        # Update task title
        self.task.title = 'Updated Task Title'
        self.task.save()
        
        # Cache should be invalidated, new title should appear
        response2 = self.client.get(reverse('tasks:task_list'), follow=True)
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, 'Updated Task Title')

    def test_task_detail_permissions_cache(self):
        """Test that task detail caching respects permissions"""
        # Create another user
        other_user = get_user_model().objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Login as task owner
        self.client.login(username='testuser', password='testpass123')
        response1 = self.client.get(reverse('tasks:task_detail', args=[self.task.id]), follow=True)
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, 'Test Task')
        
        # Login as other user
        self.client.login(username='otheruser', password='otherpass123')
        response2 = self.client.get(reverse('tasks:task_detail', args=[self.task.id]))
        self.assertEqual(response2.status_code, 403)  # Should be forbidden
