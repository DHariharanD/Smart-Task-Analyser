"""
Core scoring algorithm for task prioritization.

This module implements the intelligent scoring system that calculates
priority scores based on urgency, importance, effort, and dependencies.
"""
from datetime import datetime, timedelta
from django.utils import timezone
from typing import List, Dict, Tuple, Optional


def calculate_urgency_score(task: Dict, now: Optional[datetime] = None) -> Tuple[float, str]:
    """
    Calculate urgency score based on time until due date.
    
    Args:
        task: Task dictionary with 'due_date' and 'due_time' fields
        now: Current datetime (defaults to timezone.now())
    
    Returns:
        Tuple of (score: float, explanation: str)
        - Overdue tasks: 100 + (days_overdue * 10) with penalty
        - Future tasks: max(0, 100 - (days_until_due * 3))
    """
    if now is None:
        now = timezone.now()
    
    # Combine due_date and due_time into datetime
    due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
    due_time = datetime.strptime(task['due_time'], '%H:%M').time()
    due_datetime = datetime.combine(due_date, due_time)
    
    # Make timezone-aware if now is timezone-aware
    if timezone.is_aware(now):
        due_datetime = timezone.make_aware(due_datetime)
    
    # Calculate time difference
    time_diff = due_datetime - now
    
    if time_diff.total_seconds() < 0:
        # Task is overdue
        days_overdue = abs(time_diff.days)
        if time_diff.seconds > 0:
            days_overdue += 1  # Round up if any hours/minutes overdue
        
        urgency_score = 100 + (days_overdue * 10)
        explanation = f"Overdue by {days_overdue} day(s) (urgency: {urgency_score:.1f}/100+)"
    else:
        # Task is in the future
        days_until_due = time_diff.days
        if time_diff.seconds > 0:
            days_until_due += 1  # Round up if any hours/minutes remaining
        
        urgency_score = max(0, 100 - (days_until_due * 3))
        explanation = f"Due in {days_until_due} day(s) (urgency: {urgency_score:.1f}/100)"
    
    return urgency_score, explanation


def calculate_importance_score(task: Dict) -> Tuple[float, str]:
    """
    Calculate importance score based on user rating.
    
    Args:
        task: Task dictionary with 'importance' field (1-10)
    
    Returns:
        Tuple of (score: float, explanation: str)
        - Scales 1-10 to 0-100 (importance * 10)
    """
    importance = task.get('importance', 5)
    # Clamp to valid range
    importance = max(1, min(10, importance))
    
    importance_score = importance * 10
    explanation = f"High importance rating of {importance}/10 ({importance_score:.1f}/100)"
    
    return importance_score, explanation


def calculate_effort_score(task: Dict, max_hours: float = 40.0) -> Tuple[float, str]:
    """
    Calculate effort score (inverse - quick wins get higher scores).
    
    Args:
        task: Task dictionary with 'estimated_hours' field
        max_hours: Maximum expected hours for a task (default: 40)
    
    Returns:
        Tuple of (score: float, explanation: str)
        - Inverse scoring: ((max_hours - estimated_hours) / max_hours) * 100
    """
    estimated_hours = task.get('estimated_hours', 1.0)
    estimated_hours = max(0.1, estimated_hours)  # Ensure positive
    
    # Inverse scoring: shorter tasks get higher scores
    effort_score = ((max_hours - estimated_hours) / max_hours) * 100
    effort_score = max(0, effort_score)  # Prevent negative
    
    explanation = f"Estimated {estimated_hours:.1f} hours (effort: {effort_score:.1f}/100)"
    
    return effort_score, explanation


def calculate_dependency_score(task: Dict, all_tasks: List[Dict]) -> Tuple[float, str]:
    """
    Calculate dependency score based on how many tasks depend on this one.
    
    Args:
        task: Task dictionary with 'id' field
        all_tasks: List of all task dictionaries
    
    Returns:
        Tuple of (score: float, explanation: str)
        - Counts tasks that have this task in their dependencies
        - Score: min(100, num_dependents * 25)
    """
    task_id = task.get('id')
    if not task_id:
        return 0.0, "No dependencies (dependency: 0/100)"
    
    # Count how many tasks depend on this one
    num_dependents = 0
    for other_task in all_tasks:
        dependencies = other_task.get('dependencies', [])
        if isinstance(dependencies, list) and task_id in dependencies:
            num_dependents += 1
    
    dependency_score = min(100, num_dependents * 25)
    
    if num_dependents == 0:
        explanation = "No dependencies (dependency: 0/100)"
    else:
        explanation = f"Blocks {num_dependents} other task(s) (dependency: {dependency_score:.1f}/100)"
    
    return dependency_score, explanation


def get_strategy_weights(
    strategy: str, 
    role: Optional[str] = None,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Get weight configuration for a given strategy.
    
    Args:
        strategy: Strategy name ('smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven')
        role: User role ('developer' or 'program_manager') - only used for smart_balance
        custom_weights: Optional custom weights dict with keys 'u', 'i', 'e', 'd' (0-1 range)
    
    Returns:
        Dictionary with weights for 'u' (urgency), 'i' (importance), 
        'e' (effort), 'd' (dependency)
    """
    # If custom weights provided, use them (only for smart_balance strategy)
    if custom_weights is not None and strategy.lower() == 'smart_balance':
        # Validate custom weights sum to 1.0 (with small tolerance)
        total = sum(custom_weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Custom weights must sum to 1.0. Current sum: {total:.4f}")
        return custom_weights
    
    # Otherwise, use preset weights
    strategy_lower = strategy.lower()
    
    if strategy_lower == 'smart_balance':
        if role == 'program_manager':
            return {'u': 0.4, 'i': 0.35, 'e': 0.1, 'd': 0.15}
        else:  # developer (default)
            return {'u': 0.3, 'i': 0.3, 'e': 0.2, 'd': 0.2}
    elif strategy_lower == 'fastest_wins':
        return {'u': 0.15, 'i': 0.15, 'e': 0.6, 'd': 0.1}
    elif strategy_lower == 'high_impact':
        return {'u': 0.1, 'i': 0.7, 'e': 0.1, 'd': 0.1}
    elif strategy_lower == 'deadline_driven':
        return {'u': 0.7, 'i': 0.15, 'e': 0.05, 'd': 0.1}
    else:
        # Default to smart_balance developer
        return {'u': 0.3, 'i': 0.3, 'e': 0.2, 'd': 0.2}


def calculate_priority_score(
    task: Dict,
    all_tasks: List[Dict],
    strategy: str = 'smart_balance',
    role: Optional[str] = None,
    now: Optional[datetime] = None,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Calculate complete priority score for a task.
    
    Args:
        task: Task dictionary with all required fields
        all_tasks: List of all task dictionaries (for dependency calculation)
        strategy: Prioritization strategy name
        role: User role (for smart_balance strategy)
        now: Current datetime (for urgency calculation)
        custom_weights: Optional custom weights dict (only for smart_balance)
    
    Returns:
        Dictionary with:
        - priority_score: float (0-100+)
        - priority_label: str ('HIGH', 'MEDIUM', 'LOW')
        - component_scores: dict with individual scores
        - explanations: list of explanation strings
        - is_overdue: bool
    """
    # Get strategy weights
    weights = get_strategy_weights(strategy, role, custom_weights)
    
    # Calculate component scores
    urgency_score, urgency_explanation = calculate_urgency_score(task, now)
    importance_score, importance_explanation = calculate_importance_score(task)
    effort_score, effort_explanation = calculate_effort_score(task)
    dependency_score, dependency_explanation = calculate_dependency_score(task, all_tasks)
    
    # Calculate weighted priority score
    priority_score = (
        urgency_score * weights['u'] +
        importance_score * weights['i'] +
        effort_score * weights['e'] +
        dependency_score * weights['d']
    )
    
    # Determine priority label
    if priority_score >= 80:
        priority_label = "HIGH"
    elif priority_score >= 50:
        priority_label = "MEDIUM"
    else:
        priority_label = "LOW"
    
    # Check if overdue
    if now is None:
        now = timezone.now()
    due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
    due_time = datetime.strptime(task['due_time'], '%H:%M').time()
    due_datetime = datetime.combine(due_date, due_time)
    if timezone.is_aware(now):
        due_datetime = timezone.make_aware(due_datetime)
    is_overdue = now > due_datetime
    
    return {
        'priority_score': round(priority_score, 2),
        'priority_label': priority_label,
        'component_scores': {
            'urgency': round(urgency_score, 2),
            'importance': round(importance_score, 2),
            'effort': round(effort_score, 2),
            'dependency': round(dependency_score, 2),
        },
        'explanations': [
            urgency_explanation,
            dependency_explanation,
            importance_explanation,
            effort_explanation,
        ],
        'is_overdue': is_overdue,
    }


def generate_suggestion_explanation(
    task: Dict,
    strategy: str,
    role: Optional[str],
    component_scores: Dict[str, float],
    all_tasks: List[Dict]
) -> str:
    """
    Generate personalized explanation for why a task was suggested.
    
    Args:
        task: Task dictionary
        strategy: Prioritization strategy used
        role: User role (if Smart Balance)
        component_scores: Dictionary with 'urgency', 'importance', 'effort', 'dependency' scores
        all_tasks: All tasks for context
    
    Returns:
        Personalized explanation string (4-5 sentences)
    """
    explanations = []
    
    # Strategy and role context
    strategy_names = {
        'smart_balance': 'Smart Balance',
        'fastest_wins': 'Fastest Wins',
        'high_impact': 'High Impact',
        'deadline_driven': 'Deadline Driven'
    }
    strategy_display = strategy_names.get(strategy, strategy)
    
    if strategy == 'smart_balance' and role:
        role_display = 'Program Manager' if role == 'program_manager' else 'Developer'
        explanations.append(
            f"This task was prioritized using the {strategy_display} strategy, "
            f"which is optimized for {role_display}s."
        )
    else:
        explanations.append(
            f"This task was prioritized using the {strategy_display} strategy."
        )
    
    # Find top contributing factors
    sorted_scores = sorted(
        component_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    top_factor = sorted_scores[0]
    second_factor = sorted_scores[1] if len(sorted_scores) > 1 else None
    
    # Urgency details
    if top_factor[0] == 'urgency' or (second_factor and second_factor[0] == 'urgency'):
        urgency_score = component_scores.get('urgency', 0)
        if urgency_score >= 100:
            # Overdue
            days_overdue = int((urgency_score - 100) / 10)
            explanations.append(
                f"It's overdue by {days_overdue} day(s), making it extremely urgent "
                f"with an urgency score of {urgency_score:.1f}/100+."
            )
        else:
            days_until = int((100 - urgency_score) / 3)
            explanations.append(
                f"It's due in {days_until} day(s), giving it a high urgency score "
                f"of {urgency_score:.1f}/100."
            )
    
    # Dependency details
    if top_factor[0] == 'dependency' or (second_factor and second_factor[0] == 'dependency'):
        task_id = task.get('id')
        num_dependents = 0
        if task_id:
            for other_task in all_tasks:
                deps = other_task.get('dependencies', [])
                if isinstance(deps, list) and task_id in deps:
                    num_dependents += 1
        
        if num_dependents > 0:
            explanations.append(
                f"It blocks {num_dependents} other task(s), making it a critical "
                f"dependency with a dependency score of {component_scores.get('dependency', 0):.1f}/100."
            )
    
    # Importance details
    if top_factor[0] == 'importance' or (second_factor and second_factor[0] == 'importance'):
        importance_rating = task.get('importance', 5)
        explanations.append(
            f"It has a high importance rating of {importance_rating}/10, "
            f"contributing {component_scores.get('importance', 0):.1f}/100 to the priority score."
        )
    
    # Effort details (for fastest wins)
    if strategy == 'fastest_wins' and top_factor[0] == 'effort':
        estimated_hours = task.get('estimated_hours', 1.0)
        explanations.append(
            f"With an estimated {estimated_hours:.1f} hours, it's a quick win that "
            f"can be completed efficiently, contributing {component_scores.get('effort', 0):.1f}/100 to the score."
        )
    
    # Role-specific reasoning
    if strategy == 'smart_balance' and role:
        if role == 'program_manager':
            if top_factor[0] in ['urgency', 'importance']:
                explanations.append(
                    "For Program Managers, urgent and high-importance tasks are weighted "
                    "more heavily to ensure stakeholder needs and deadlines are met."
                )
        else:  # developer
            if top_factor[0] in ['dependency', 'effort']:
                explanations.append(
                    "For Developers, tasks that block other work or can be completed quickly "
                    "are prioritized to maintain development momentum."
                )
    
    # Combine explanations
    return " ".join(explanations)


def detect_circular_dependencies(tasks: List[Dict]) -> Dict:
    """
    Detect circular dependencies in task list using DFS algorithm.
    
    Args:
        tasks: List of task dictionaries with 'id', 'title', and 'dependencies' fields
    
    Returns:
        Dictionary with:
        - chains: List of circular dependency chains as formatted strings with task titles
        - affected_task_ids: Set of all task IDs involved in cycles
        - cycles: List of cycle lists (each cycle is a list of task IDs)
    """
    # Build task lookup for titles
    task_lookup = {}
    for task in tasks:
        task_id = task.get('id')
        if task_id:
            task_lookup[task_id] = {
                'title': task.get('title', task_id),
                'id': task_id
            }
    
    # Build adjacency list: task_id -> list of dependent task IDs
    graph = {}
    task_ids = set()
    
    for task in tasks:
        task_id = task.get('id')
        if not task_id:
            continue
        
        task_ids.add(task_id)
        dependencies = task.get('dependencies', [])
        if not isinstance(dependencies, list):
            dependencies = []
        
        # Build reverse graph: which tasks depend on this one
        for dep_id in dependencies:
            if dep_id not in graph:
                graph[dep_id] = []
            graph[dep_id].append(task_id)
    
    circular_chains = []
    cycles = []
    affected_task_ids = set()
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(node: str) -> bool:
        """DFS to detect cycles."""
        if node in rec_stack:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            
            # Store cycle as list of IDs
            cycles.append(cycle.copy())
            
            # Add all nodes in cycle to affected set
            for cycle_node in cycle:
                affected_task_ids.add(cycle_node)
            
            # Format cycle with task titles
            cycle_titles = []
            for cycle_id in cycle:
                if cycle_id in task_lookup:
                    title = task_lookup[cycle_id]['title']
                    cycle_titles.append(f"{title} ({cycle_id})")
                else:
                    cycle_titles.append(cycle_id)
            
            # Create formatted chain string
            chain_str = " → ".join(cycle_titles)
            if chain_str not in circular_chains:
                circular_chains.append(chain_str)
            
            return True
        
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        # Visit all tasks that depend on this node
        if node in graph:
            for neighbor in graph[node]:
                dfs(neighbor)
        
        rec_stack.remove(node)
        path.pop()
        return False
    
    # Check all tasks
    for task_id in task_ids:
        if task_id not in visited:
            dfs(task_id)
    
    return {
        'chains': circular_chains,
        'affected_task_ids': list(affected_task_ids),
        'cycles': cycles
    }


def analyze_tasks(
    tasks: List[Dict],
    strategy: str = 'smart_balance',
    role: Optional[str] = None,
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Main function to analyze and score all tasks.
    
    Args:
        tasks: List of task dictionaries
        strategy: Prioritization strategy
        role: User role (for smart_balance strategy)
        custom_weights: Optional custom weights dict (only for smart_balance)
    
    Returns:
        Dictionary with:
        - tasks: List of tasks with priority scores and explanations
        - circular_dependencies: List of circular dependency chains
        - warnings: List of warning messages
    """
    if not tasks:
        return {
            'tasks': [],
            'circular_dependencies': [],
            'affected_task_ids': [],
            'circular_warning': None,
            'warnings': ['No tasks provided'],
        }
    
    now = timezone.now()
    
    # Detect circular dependencies
    circular_deps_result = detect_circular_dependencies(tasks)
    circular_dependencies = circular_deps_result['chains']
    affected_task_ids = circular_deps_result['affected_task_ids']
    
    # Calculate priority scores for all tasks
    analyzed_tasks = []
    overdue_count = 0
    
    for task in tasks:
        # Apply defaults for missing data
        task_with_defaults = {
            'id': task.get('id', f"task_{len(analyzed_tasks)}"),
            'title': task.get('title', 'Untitled Task'),
            'due_date': task.get('due_date'),
            'due_time': task.get('due_time', '23:59'),
            'estimated_hours': task.get('estimated_hours', 1.0),
            'importance': task.get('importance', 5),
            'dependencies': task.get('dependencies', []),
            'role': task.get('role', 'developer'),
            'notes': task.get('notes', ''),
        }
        
        # Default due_date to 7 days from now if missing
        if not task_with_defaults['due_date']:
            default_date = (now + timedelta(days=7)).date()
            task_with_defaults['due_date'] = default_date.strftime('%Y-%m-%d')
        
        # Calculate priority
        priority_data = calculate_priority_score(
            task_with_defaults,
            tasks,
            strategy,
            role,
            now,
            custom_weights
        )
        
        # Merge task data with priority data
        analyzed_task = {
            **task_with_defaults,
            **priority_data,
        }
        
        if priority_data['is_overdue']:
            overdue_count += 1
        
        analyzed_tasks.append(analyzed_task)
    
    # Sort by priority score (descending)
    analyzed_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
    
    # Generate warnings
    warnings = []
    if overdue_count > 0:
        warnings.append(f"{overdue_count} task(s) are overdue")
    if circular_dependencies:
        warnings.append(f"{len(circular_dependencies)} circular dependency chain(s) detected")
    
    # Create human-readable warning message for circular dependencies
    circular_warning = None
    if circular_dependencies:
        if len(circular_dependencies) == 1:
            circular_warning = f"Circular dependency detected: {circular_dependencies[0]}. Break the cycle by removing one dependency."
        else:
            circular_warning = f"{len(circular_dependencies)} circular dependencies detected. Break the cycles by removing dependencies."
    
    return {
        'tasks': analyzed_tasks,
        'circular_dependencies': circular_dependencies,
        'affected_task_ids': affected_task_ids,
        'circular_warning': circular_warning,
        'warnings': warnings,
    }
