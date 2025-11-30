"""
Task model for Smart Task Analyzer.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, time


class Task(models.Model):
    """
    Task model with all required fields for priority analysis.
    """
    ROLE_CHOICES = [
        ('developer', 'Developer'),
        ('program_manager', 'Program Manager'),
    ]
    
    title = models.CharField(max_length=200, help_text="Task title")
    due_date = models.DateField(help_text="Due date (YYYY-MM-DD)")
    due_time = models.TimeField(help_text="Due time (HH:MM)")
    estimated_hours = models.FloatField(
        validators=[MinValueValidator(0.1)],
        help_text="Estimated hours to complete (must be > 0)"
    )
    importance = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Importance rating (1-10)"
    )
    dependencies = models.JSONField(
        default=list,
        blank=True,
        help_text="List of task IDs this task depends on"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='developer',
        help_text="User role for strategy selection"
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text="Additional notes or description for the task"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} (Due: {self.due_date})"
    
    @property
    def due_datetime(self):
        """Combine due_date and due_time into a datetime object."""
        return datetime.combine(self.due_date, self.due_time)
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        now = timezone.now()
        due = timezone.make_aware(self.due_datetime)
        return now > due
    
    def clean(self):
        """Validate model data."""
        from django.core.exceptions import ValidationError
        
        # Ensure importance is within valid range
        if self.importance < 1 or self.importance > 10:
            raise ValidationError({
                'importance': 'Importance must be between 1 and 10.'
            })
        
        # Ensure estimated_hours is positive
        if self.estimated_hours <= 0:
            raise ValidationError({
                'estimated_hours': 'Estimated hours must be greater than 0.'
            })
        
        # Validate dependencies is a list
        if not isinstance(self.dependencies, list):
            raise ValidationError({
                'dependencies': 'Dependencies must be a list of task IDs.'
            })
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)

