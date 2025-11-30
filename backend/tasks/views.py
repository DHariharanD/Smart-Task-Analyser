"""
API views for task analysis endpoints.
"""
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser
from .models import Task
from .serializers import TaskAnalyzeRequestSerializer, TaskSuggestRequestSerializer, TaskSerializer
from .scoring import analyze_tasks, generate_suggestion_explanation


class TaskAnalyzeView(APIView):
    """
    POST /api/tasks/analyze/
    
    Analyze and score tasks based on selected strategy.
    
    Request Body:
    {
        "tasks": [
            {
                "id": "task_1",
                "title": "Complete feature X",
                "due_date": "2024-12-31",
                "due_time": "17:00",
                "estimated_hours": 8.0,
                "importance": 9,
                "dependencies": [],
                "role": "developer"
            }
        ],
        "strategy": "smart_balance",
        "role": "developer"
    }
    
    Response:
    {
        "tasks": [...sorted tasks with scores...],
        "circular_dependencies": [...],
        "warnings": [...]
    }
    """
    parser_classes = [JSONParser]
    
    def post(self, request):
        """Analyze tasks and return sorted results with scores."""
        try:
            # Validate input
            serializer = TaskAnalyzeRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'error': 'Validation failed',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            tasks = validated_data['tasks']
            strategy = validated_data.get('strategy', 'smart_balance')
            role = validated_data.get('role', 'developer')
            custom_weights = validated_data.get('custom_weights')
            
            # Validate custom_weights only for smart_balance strategy
            if custom_weights is not None and strategy != 'smart_balance':
                return Response(
                    {
                        'error': 'Invalid request',
                        'message': 'Custom weights can only be used with Smart Balance strategy'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert serializer data to dict format expected by scoring module
            task_dicts = []
            for task in tasks:
                task_dict = {
                    'id': task.get('id'),
                    'title': task.get('title'),
                    'due_date': task.get('due_date'),
                    'due_time': task.get('due_time'),
                    'estimated_hours': task.get('estimated_hours'),
                    'importance': task.get('importance'),
                    'dependencies': task.get('dependencies', []),
                    'role': task.get('role', 'developer'),
                    'notes': task.get('notes', ''),
                }
                task_dicts.append(task_dict)
            
            # Analyze tasks using scoring module
            try:
                result = analyze_tasks(
                    tasks=task_dicts,
                    strategy=strategy,
                    role=role,
                    custom_weights=custom_weights
                )
                
                # Debug: Check if notes are in the result
                if result['tasks']:
                    print(f"DEBUG ANALYZE RESPONSE: First task keys: {result['tasks'][0].keys()}")
                    print(f"DEBUG ANALYZE RESPONSE: First task notes: '{result['tasks'][0].get('notes', 'MISSING')}'")
                
            except ValueError as e:
                # Handle validation errors from get_strategy_weights
                return Response(
                    {
                        'error': 'Invalid custom weights',
                        'message': str(e)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except json.JSONDecodeError:
            return Response(
                {
                    'error': 'Invalid JSON',
                    'message': 'Request body must be valid JSON'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Internal server error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskSuggestView(APIView):
    """
    GET /api/tasks/suggest/
    
    Get top 3 task suggestions for today.
    
    Query Parameters (JSON encoded):
    - tasks: JSON array of tasks (required)
    - strategy: Prioritization strategy (optional, default: smart_balance)
    - role: User role (optional, default: developer)
    
    OR
    
    POST /api/tasks/suggest/
    
    Request Body: Same as /api/tasks/analyze/
    
    Response:
    {
        "suggestions": [...top 3 tasks...],
        "strategy": "smart_balance",
        "role": "developer"
    }
    """
    parser_classes = [JSONParser]
    
    def get(self, request):
        """Handle GET request with tasks in query parameter."""
        try:
            # Get tasks from query parameter
            tasks_json = request.query_params.get('tasks')
            if not tasks_json:
                return Response(
                    {
                        'error': 'Missing tasks parameter',
                        'message': 'Please provide tasks as JSON in query parameter: ?tasks=[...]'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Parse tasks JSON
            try:
                tasks_data = json.loads(tasks_json)
            except json.JSONDecodeError:
                return Response(
                    {
                        'error': 'Invalid JSON in tasks parameter',
                        'message': 'Tasks must be valid JSON array'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate using serializer
            request_data = {
                'tasks': tasks_data,
                'strategy': request.query_params.get('strategy', 'smart_balance'),
                'role': request.query_params.get('role', 'developer'),
            }
            
            serializer = TaskSuggestRequestSerializer(data=request_data)
            if not serializer.is_valid():
                return Response(
                    {
                        'error': 'Validation failed',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return self._process_suggestions(serializer.validated_data)
            
        except Exception as e:
            return Response(
                {
                    'error': 'Internal server error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Handle POST request with tasks in body."""
        try:
            # Validate input
            serializer = TaskSuggestRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'error': 'Validation failed',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return self._process_suggestions(serializer.validated_data)
            
        except json.JSONDecodeError:
            return Response(
                {
                    'error': 'Invalid JSON',
                    'message': 'Request body must be valid JSON'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Internal server error',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_suggestions(self, validated_data):
        """Process task suggestions and return top 3."""
        try:
            tasks = validated_data['tasks']
            strategy = validated_data.get('strategy', 'smart_balance')
            role = validated_data.get('role', 'developer')
            custom_weights = validated_data.get('custom_weights')
            
            # Validate custom_weights only for smart_balance strategy
            if custom_weights is not None and strategy != 'smart_balance':
                return Response(
                    {
                        'error': 'Invalid request',
                        'message': 'Custom weights can only be used with Smart Balance strategy'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert serializer data to dict format expected by scoring module
            task_dicts = []
            for task in tasks:
                task_dict = {
                    'id': task.get('id'),
                    'title': task.get('title'),
                    'due_date': task.get('due_date'),
                    'due_time': task.get('due_time'),
                    'estimated_hours': task.get('estimated_hours'),
                    'importance': task.get('importance'),
                    'dependencies': task.get('dependencies', []),
                    'role': task.get('role', 'developer'),
                    'notes': task.get('notes', ''),
                }
                task_dicts.append(task_dict)
            
            # Analyze tasks
            try:
                result = analyze_tasks(
                    tasks=task_dicts,
                    strategy=strategy,
                    role=role,
                    custom_weights=custom_weights
                )
            except ValueError as e:
                # Handle validation errors from get_strategy_weights
                return Response(
                    {
                        'error': 'Invalid custom weights',
                        'message': str(e)
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get top 3 tasks
            top_3 = result['tasks'][:3]
            
            # Generate personalized explanations for each suggestion
            suggestions_with_explanations = []
            for task in top_3:
                explanation = generate_suggestion_explanation(
                    task=task,
                    strategy=strategy,
                    role=role,
                    component_scores=task.get('component_scores', {}),
                    all_tasks=task_dicts
                )
                
                suggestion = {
                    **task,
                    'explanation': explanation
                }
                suggestions_with_explanations.append(suggestion)
            
            return Response(
                {
                    'suggestions': suggestions_with_explanations,
                    'strategy': strategy,
                    'role': role,
                    'total_tasks': len(result['tasks']),
                    'warnings': result.get('warnings', [])
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to process suggestions',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskListCreateView(APIView):
    """
    GET /api/tasks/ - List all tasks
    POST /api/tasks/ - Create a new task
    """
    parser_classes = [JSONParser]
    
    def get(self, request):
        """Get all tasks from database."""
        try:
            tasks = Task.objects.all()
            serializer = TaskSerializer(tasks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to retrieve tasks',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Create a new task in database."""
        try:
            serializer = TaskSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'error': 'Validation failed',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            task = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {
                    'error': 'Failed to create task',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskDetailView(APIView):
    """
    GET /api/tasks/{id}/ - Get a specific task
    PUT /api/tasks/{id}/ - Update a task
    DELETE /api/tasks/{id}/ - Delete a task
    """
    parser_classes = [JSONParser]
    
    def get_object(self, pk):
        """Helper method to get task by ID."""
        try:
            return Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return None
    
    def get(self, request, pk):
        """Get a specific task."""
        task = self.get_object(pk)
        if not task:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """Update a task."""
        task = self.get_object(pk)
        if not task:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TaskSerializer(task, data=request.data, partial=True)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Validation failed',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        """Delete a task."""
        task = self.get_object(pk)
        if not task:
            return Response(
                {'error': 'Task not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        task.delete()
        return Response(
            {'message': 'Task deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
