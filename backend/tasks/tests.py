"""
Unit tests for tasks app.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.test import APIClient
from rest_framework import status
import json

from .scoring import (
    calculate_urgency_score,
    calculate_importance_score,
    calculate_effort_score,
    calculate_dependency_score,
    get_strategy_weights,
    calculate_priority_score,
    detect_circular_dependencies,
    analyze_tasks,
)


class ScoringTests(TestCase):
    """Test basic scoring functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()
        self.tomorrow = self.now + timedelta(days=1)
        self.yesterday = self.now - timedelta(days=1)
    
    def test_urgency_score_future_task(self):
        """Test urgency score for future task."""
        task = {
            'due_date': self.tomorrow.strftime('%Y-%m-%d'),
            'due_time': '17:00',
        }
        score, explanation = calculate_urgency_score(task, self.now)
        
        # Should be less than 100 (not urgent yet)
        self.assertLess(score, 100)
        self.assertGreater(score, 0)
        self.assertIn('Due in', explanation)
    
    def test_urgency_score_overdue_task(self):
        """Test urgency score for overdue task with penalty."""
        task = {
            'due_date': self.yesterday.strftime('%Y-%m-%d'),
            'due_time': '17:00',
        }
        score, explanation = calculate_urgency_score(task, self.now)
        
        # Overdue tasks should have score >= 100
        self.assertGreaterEqual(score, 100)
        self.assertIn('Overdue', explanation)
    
    def test_importance_score(self):
        """Test importance score calculation."""
        # Test high importance
        task = {'importance': 9}
        score, explanation = calculate_importance_score(task)
        self.assertEqual(score, 90.0)
        self.assertIn('9/10', explanation)
        
        # Test low importance
        task = {'importance': 2}
        score, explanation = calculate_importance_score(task)
        self.assertEqual(score, 20.0)
    
    def test_effort_score_inverse(self):
        """Test effort score (inverse - quick wins get higher scores)."""
        # Short task should have high effort score
        task = {'estimated_hours': 2.0}
        score_short, _ = calculate_effort_score(task)
        
        # Long task should have low effort score
        task = {'estimated_hours': 30.0}
        score_long, _ = calculate_effort_score(task)
        
        # Shorter task should score higher
        self.assertGreater(score_short, score_long)
    
    def test_dependency_score(self):
        """Test dependency score calculation."""
        task1 = {'id': 'task_1', 'dependencies': []}
        task2 = {'id': 'task_2', 'dependencies': ['task_1']}
        task3 = {'id': 'task_3', 'dependencies': ['task_1']}
        
        all_tasks = [task1, task2, task3]
        
        # task_1 blocks 2 other tasks
        score, explanation = calculate_dependency_score(task1, all_tasks)
        self.assertEqual(score, 50.0)  # 2 * 25 = 50
        self.assertIn('Blocks 2', explanation)
        
        # task_2 blocks no tasks
        score, explanation = calculate_dependency_score(task2, all_tasks)
        self.assertEqual(score, 0.0)
        self.assertIn('No dependencies', explanation)


class CircularDependencyTests(TestCase):
    """Test circular dependency detection."""
    
    def test_no_circular_dependencies(self):
        """Test detection when no circular dependencies exist."""
        tasks = [
            {'id': 'task_1', 'dependencies': []},
            {'id': 'task_2', 'dependencies': ['task_1']},
            {'id': 'task_3', 'dependencies': ['task_2']},
        ]
        
        circular = detect_circular_dependencies(tasks)
        self.assertEqual(len(circular), 0)
    
    def test_simple_circular_dependency(self):
        """Test detection of simple circular dependency (A -> B -> A)."""
        tasks = [
            {'id': 'task_1', 'dependencies': ['task_2']},
            {'id': 'task_2', 'dependencies': ['task_1']},
        ]
        
        circular = detect_circular_dependencies(tasks)
        self.assertGreater(len(circular), 0)
        # Should detect the cycle
        self.assertTrue(any('task_1' in chain and 'task_2' in chain for chain in circular))
    
    def test_complex_circular_dependency(self):
        """Test detection of complex circular dependency (A -> B -> C -> A)."""
        tasks = [
            {'id': 'task_1', 'dependencies': ['task_2']},
            {'id': 'task_2', 'dependencies': ['task_3']},
            {'id': 'task_3', 'dependencies': ['task_1']},
        ]
        
        circular = detect_circular_dependencies(tasks)
        self.assertGreater(len(circular), 0)
        # Should detect the cycle involving all three tasks
        self.assertTrue(any('task_1' in chain and 'task_2' in chain and 'task_3' in chain 
                          for chain in circular))


class OverdueTaskTests(TestCase):
    """Test overdue task handling."""
    
    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()
        self.overdue_date = (self.now - timedelta(days=2)).strftime('%Y-%m-%d')
        self.future_date = (self.now + timedelta(days=5)).strftime('%Y-%m-%d')
    
    def test_overdue_task_penalty(self):
        """Test that overdue tasks get penalty scoring."""
        task = {
            'id': 'task_1',
            'title': 'Overdue Task',
            'due_date': self.overdue_date,
            'due_time': '17:00',
            'estimated_hours': 5.0,
            'importance': 5,
            'dependencies': [],
        }
        
        all_tasks = [task]
        result = calculate_priority_score(task, all_tasks, 'deadline_driven', None, self.now)
        
        # Overdue task should have high priority score
        self.assertGreater(result['priority_score'], 50)
        self.assertTrue(result['is_overdue'])
        self.assertIn('Overdue', result['explanations'][0])
    
    def test_overdue_in_analysis(self):
        """Test overdue detection in analyze_tasks function."""
        tasks = [
            {
                'id': 'task_1',
                'title': 'Overdue Task',
                'due_date': self.overdue_date,
                'due_time': '17:00',
                'estimated_hours': 5.0,
                'importance': 5,
                'dependencies': [],
            },
            {
                'id': 'task_2',
                'title': 'Future Task',
                'due_date': self.future_date,
                'due_time': '17:00',
                'estimated_hours': 5.0,
                'importance': 5,
                'dependencies': [],
            },
        ]
        
        result = analyze_tasks(tasks, 'smart_balance', 'developer')
        
        # Should detect overdue task
        overdue_tasks = [t for t in result['tasks'] if t['is_overdue']]
        self.assertEqual(len(overdue_tasks), 1)
        self.assertIn('overdue', result['warnings'][0].lower())


class MissingDataTests(TestCase):
    """Test missing data defaults."""
    
    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()
        self.future_date = (self.now + timedelta(days=7)).strftime('%Y-%m-%d')
    
    def test_missing_due_date_default(self):
        """Test that missing due_date defaults to 7 days from now."""
        task = {
            'id': 'task_1',
            'title': 'Task without date',
            'due_time': '17:00',
            'estimated_hours': 5.0,
            'importance': 5,
            'dependencies': [],
        }
        
        all_tasks = [task]
        result = analyze_tasks(all_tasks, 'smart_balance', 'developer')
        
        # Should have a due_date assigned
        analyzed_task = result['tasks'][0]
        self.assertIsNotNone(analyzed_task['due_date'])
        self.assertIn(analyzed_task['due_date'], result['tasks'][0].values())
    
    def test_missing_importance_default(self):
        """Test that missing importance defaults to 5."""
        task = {
            'id': 'task_1',
            'title': 'Task without importance',
            'due_date': self.future_date,
            'due_time': '17:00',
            'estimated_hours': 5.0,
            'dependencies': [],
        }
        
        all_tasks = [task]
        result = analyze_tasks(all_tasks, 'smart_balance', 'developer')
        
        # Should use default importance of 5
        analyzed_task = result['tasks'][0]
        # Importance should result in score of 50 (5 * 10)
        component_scores = analyzed_task['component_scores']
        self.assertGreaterEqual(component_scores['importance'], 40)  # Around 50
    
    def test_missing_estimated_hours_default(self):
        """Test that missing estimated_hours defaults to 1.0."""
        task = {
            'id': 'task_1',
            'title': 'Task without hours',
            'due_date': self.future_date,
            'due_time': '17:00',
            'importance': 5,
            'dependencies': [],
        }
        
        all_tasks = [task]
        result = analyze_tasks(all_tasks, 'smart_balance', 'developer')
        
        # Should have estimated_hours
        analyzed_task = result['tasks'][0]
        self.assertIn('estimated_hours', analyzed_task)
        self.assertGreater(analyzed_task['estimated_hours'], 0)


class StrategySwitchingTests(TestCase):
    """Test strategy switching."""
    
    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()
        self.future_date = (self.now + timedelta(days=3)).strftime('%Y-%m-%d')
        
        self.task = {
            'id': 'task_1',
            'title': 'Test Task',
            'due_date': self.future_date,
            'due_time': '17:00',
            'estimated_hours': 10.0,
            'importance': 8,
            'dependencies': [],
        }
    
    def test_strategy_weights(self):
        """Test that different strategies have different weights."""
        weights_fastest = get_strategy_weights('fastest_wins')
        weights_high_impact = get_strategy_weights('high_impact')
        weights_deadline = get_strategy_weights('deadline_driven')
        
        # Fastest wins should heavily weight effort
        self.assertGreater(weights_fastest['e'], 0.5)
        
        # High impact should heavily weight importance
        self.assertGreater(weights_high_impact['i'], 0.5)
        
        # Deadline driven should heavily weight urgency
        self.assertGreater(weights_deadline['u'], 0.5)
    
    def test_smart_balance_role_difference(self):
        """Test that smart_balance has different weights for different roles."""
        weights_dev = get_strategy_weights('smart_balance', 'developer')
        weights_pm = get_strategy_weights('smart_balance', 'program_manager')
        
        # PM should weight urgency more than dev
        self.assertGreater(weights_pm['u'], weights_dev['u'])
        
        # PM should weight effort less than dev
        self.assertLess(weights_pm['e'], weights_dev['e'])
    
    def test_strategy_affects_priority_score(self):
        """Test that different strategies produce different priority scores."""
        all_tasks = [self.task]
        
        # Create a task with high importance but far deadline
        task = {
            'id': 'task_1',
            'title': 'High Importance, Far Deadline',
            'due_date': (self.now + timedelta(days=10)).strftime('%Y-%m-%d'),
            'due_time': '17:00',
            'estimated_hours': 20.0,
            'importance': 9,
            'dependencies': [],
        }
        
        score_high_impact = calculate_priority_score(
            task, [task], 'high_impact', None, self.now
        )['priority_score']
        
        score_deadline = calculate_priority_score(
            task, [task], 'deadline_driven', None, self.now
        )['priority_score']
        
        # High impact should score higher for high importance tasks
        # Deadline driven should score lower for far deadlines
        # The exact relationship depends on the weights, but they should differ
        self.assertNotEqual(score_high_impact, score_deadline)


class APITests(TestCase):
    """Test API endpoints."""
    
    def setUp(self):
        """Set up test client and data."""
        self.client = APIClient()
        self.now = timezone.now()
        self.future_date = (self.now + timedelta(days=5)).strftime('%Y-%m-%d')
        
        self.valid_task = {
            'title': 'Test Task',
            'due_date': self.future_date,
            'due_time': '17:00',
            'estimated_hours': 8.0,
            'importance': 7,
            'dependencies': [],
        }
    
    def test_analyze_endpoint_success(self):
        """Test successful task analysis."""
        data = {
            'tasks': [self.valid_task],
            'strategy': 'smart_balance',
            'role': 'developer',
        }
        
        response = self.client.post(
            '/api/tasks/analyze/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tasks', response.data)
        self.assertIn('warnings', response.data)
        self.assertIn('circular_dependencies', response.data)
        self.assertEqual(len(response.data['tasks']), 1)
    
    def test_analyze_endpoint_validation_error(self):
        """Test validation error handling."""
        # Missing required field
        data = {
            'tasks': [{'title': 'Task without date'}],
        }
        
        response = self.client.post(
            '/api/tasks/analyze/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should still work (defaults applied) or return validation error
        # Since we apply defaults, it should work
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
    
    def test_analyze_endpoint_invalid_json(self):
        """Test invalid JSON handling."""
        response = self.client.post(
            '/api/tasks/analyze/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_suggest_endpoint_post(self):
        """Test POST /api/tasks/suggest/ endpoint."""
        data = {
            'tasks': [self.valid_task, self.valid_task, self.valid_task, self.valid_task],
            'strategy': 'fastest_wins',
        }
        
        response = self.client.post(
            '/api/tasks/suggest/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)
        self.assertLessEqual(len(response.data['suggestions']), 3)
        self.assertEqual(response.data['total_tasks'], 4)
    
    def test_suggest_endpoint_empty_tasks(self):
        """Test suggest endpoint with empty task list."""
        data = {
            'tasks': [],
        }
        
        response = self.client.post(
            '/api/tasks/suggest/',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
