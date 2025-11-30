"""
Serializers for task API endpoints.
"""
from rest_framework import serializers
from datetime import datetime, date, time
import re
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model - used for CRUD operations.
    """
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'due_date', 'due_time', 'estimated_hours',
            'importance', 'dependencies', 'role', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def to_representation(self, instance):
        """Convert model instance to dict format for API response."""
        data = super().to_representation(instance)
        # Convert date and time to string format
        if isinstance(data.get('due_date'), date):
            data['due_date'] = data['due_date'].strftime('%Y-%m-%d')
        if isinstance(data.get('due_time'), time):
            data['due_time'] = data['due_time'].strftime('%H:%M')
        return data


class TaskInputSerializer(serializers.Serializer):
    """
    Serializer for task input validation.
    Handles both single task and bulk task input.
    """
    id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(required=True, max_length=200)
    due_date = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    due_time = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    estimated_hours = serializers.FloatField(required=False, min_value=0.1)
    importance = serializers.IntegerField(required=False, min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    role = serializers.ChoiceField(
        choices=['developer', 'program_manager'],
        required=False,
        default='developer'
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        default=''
    )
    created_at = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate_due_date(self, value):
        """Validate date format YYYY-MM-DD."""
        if not value:
            return None
        
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError:
            raise serializers.ValidationError(
                "Date must be in YYYY-MM-DD format (e.g., 2024-12-31)"
            )
    
    def validate_due_time(self, value):
        """Validate time format HH:MM or HH:MM:SS."""
        if not value:
            return None
        
        # Accept both HH:MM and HH:MM:SS formats (database returns with seconds)
        if not re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$', value):
            raise serializers.ValidationError(
                "Time must be in HH:MM format (e.g., 14:30)"
            )
        
        # Strip seconds if present to normalize format
        if len(value) == 8:  # HH:MM:SS format
            value = value[:5]  # Convert to HH:MM
        
        return value
    
    def validate_estimated_hours(self, value):
        """Ensure estimated_hours is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Estimated hours must be greater than 0"
            )
        return value
    
    def validate_importance(self, value):
        """Clamp importance to valid range."""
        if value is not None:
            return max(1, min(10, value))
        return value
    
    def validate_dependencies(self, value):
        """Ensure dependencies is a list."""
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Dependencies must be a list")
        return value


class TaskAnalyzeRequestSerializer(serializers.Serializer):
    """
    Serializer for POST /api/tasks/analyze/ request.
    """
    tasks = serializers.ListField(
        child=TaskInputSerializer(),
        required=True,
        min_length=1,
        error_messages={
            'required': 'Tasks list is required',
            'min_length': 'At least one task is required'
        }
    )
    strategy = serializers.ChoiceField(
        choices=['smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'],
        required=False,
        default='smart_balance'
    )
    role = serializers.ChoiceField(
        choices=['developer', 'program_manager'],
        required=False,
        default='developer'
    )
    custom_weights = serializers.DictField(
        required=False,
        allow_null=True
    )
    
    def validate_tasks(self, value):
        """Validate that tasks list is not empty."""
        if not value:
            raise serializers.ValidationError("At least one task is required")
        return value
    
    def validate_custom_weights(self, value):
        """Validate custom weights if provided."""
        if value is None:
            return value
        
        # Check all required keys are present
        required_keys = ['urgency', 'importance', 'effort', 'dependencies']
        if not all(key in value for key in required_keys):
            raise serializers.ValidationError(
                "Custom weights must include: urgency, importance, effort, dependencies"
            )
        
        # Validate each weight is between 0-100
        for key, weight in value.items():
            if not isinstance(weight, (int, float)):
                raise serializers.ValidationError(f"Weight '{key}' must be a number")
            if weight < 0 or weight > 100:
                raise serializers.ValidationError(
                    f"Weight '{key}' must be between 0 and 100"
                )
        
        # Validate weights sum to 100
        total = sum(value.values())
        if abs(total - 100) > 0.01:  # Allow small floating point differences
            raise serializers.ValidationError(
                f"Weights must sum to 100%. Current sum: {total:.2f}%"
            )
        
        # Convert to decimal format (0-1 range) for internal use
        return {
            'u': value['urgency'] / 100.0,
            'i': value['importance'] / 100.0,
            'e': value['effort'] / 100.0,
            'd': value['dependencies'] / 100.0,
        }


class TaskSuggestRequestSerializer(serializers.Serializer):
    """
    Serializer for GET /api/tasks/suggest/ request.
    Accepts tasks as query parameter or in request body.
    """
    tasks = serializers.ListField(
        child=TaskInputSerializer(),
        required=True,
        min_length=1
    )
    strategy = serializers.ChoiceField(
        choices=['smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'],
        required=False,
        default='smart_balance'
    )
    role = serializers.ChoiceField(
        choices=['developer', 'program_manager'],
        required=False,
        default='developer'
    )
    custom_weights = serializers.DictField(
        required=False,
        allow_null=True
    )
    
    def validate_custom_weights(self, value):
        """Validate custom weights if provided."""
        if value is None:
            return value
        
        # Check all required keys are present
        required_keys = ['urgency', 'importance', 'effort', 'dependencies']
        if not all(key in value for key in required_keys):
            raise serializers.ValidationError(
                "Custom weights must include: urgency, importance, effort, dependencies"
            )
        
        # Validate each weight is between 0-100
        for key, weight in value.items():
            if not isinstance(weight, (int, float)):
                raise serializers.ValidationError(f"Weight '{key}' must be a number")
            if weight < 0 or weight > 100:
                raise serializers.ValidationError(
                    f"Weight '{key}' must be between 0 and 100"
                )
        
        # Validate weights sum to 100
        total = sum(value.values())
        if abs(total - 100) > 0.01:  # Allow small floating point differences
            raise serializers.ValidationError(
                f"Weights must sum to 100%. Current sum: {total:.2f}%"
            )
        
        # Convert to decimal format (0-1 range) for internal use
        return {
            'u': value['urgency'] / 100.0,
            'i': value['importance'] / 100.0,
            'e': value['effort'] / 100.0,
            'd': value['dependencies'] / 100.0,
        }
