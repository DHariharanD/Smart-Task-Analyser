# Algorithm Explanation

## Overview

The Smart Task Analyzer uses a sophisticated multi-factor scoring algorithm to calculate priority scores for tasks. The algorithm considers four key dimensions: urgency, importance, effort, and dependencies. Each dimension is scored independently (0-100 scale), then combined using strategy-specific weights to produce a final priority score.

## Component Scores

### 1. Urgency Score (0-100+)

The urgency score measures how time-sensitive a task is based on its due date and time.

**Formula for Future Tasks:**
```
urgency_score = max(0, 100 - (days_until_due * 3))
```

Tasks due soon receive higher urgency scores. For example:
- Due today: ~100 points
- Due in 1 day: ~97 points
- Due in 10 days: ~70 points
- Due in 33+ days: 0 points

**Formula for Overdue Tasks:**
```
urgency_score = 100 + (days_overdue * 10)
```

Overdue tasks receive penalty scoring that increases with each passing day:
- 1 day overdue: 110 points
- 2 days overdue: 120 points
- 5 days overdue: 150 points

This penalty system ensures overdue tasks are prioritized and addressed quickly.

### 2. Importance Score (0-100)

The importance score directly maps the user's importance rating to a 0-100 scale.

**Formula:**
```
importance_score = importance_rating * 10
```

Where `importance_rating` is the user's input (1-10 scale):
- Rating 1: 10 points
- Rating 5: 50 points
- Rating 10: 100 points

This linear mapping ensures that user-perceived importance directly influences the final priority score.

### 3. Effort Score (0-100)

The effort score uses inverse scoring to prioritize "quick wins" - tasks that can be completed quickly.

**Formula:**
```
effort_score = ((max_hours - estimated_hours) / max_hours) * 100
```

Where `max_hours` defaults to 40 (configurable). Shorter tasks receive higher scores:
- 1 hour task: ~97.5 points
- 5 hour task: ~87.5 points
- 20 hour task: 50 points
- 40+ hour task: 0 points

This encourages completing smaller tasks first, which can provide momentum and clear the task list faster.

### 4. Dependency Score (0-100)

The dependency score measures how many other tasks depend on completing this task.

**Formula:**
```
dependency_score = min(100, num_dependents * 25)
```

Tasks that block other work receive higher scores:
- Blocks 1 task: 25 points
- Blocks 2 tasks: 50 points
- Blocks 3 tasks: 75 points
- Blocks 4+ tasks: 100 points (capped)

This ensures that critical path tasks (those blocking other work) are prioritized appropriately.

## Strategy Weights

Different prioritization strategies use different weight combinations to emphasize different factors:

### Smart Balance (Developer)
- Urgency: 30%
- Importance: 30%
- Effort: 20%
- Dependencies: 20%

Balanced approach suitable for developers who need to balance multiple concerns.

### Smart Balance (Program Manager)
- Urgency: 40%
- Importance: 35%
- Effort: 10%
- Dependencies: 15%

Emphasizes urgency and importance more, suitable for program managers managing deadlines and stakeholder needs.

### Fastest Wins
- Urgency: 15%
- Importance: 15%
- Effort: 60%
- Dependencies: 10%

Heavily prioritizes quick tasks to build momentum and clear the backlog.

### High Impact
- Urgency: 10%
- Importance: 70%
- Effort: 10%
- Dependencies: 10%

Focuses on high-importance tasks regardless of urgency or effort.

### Deadline Driven
- Urgency: 70%
- Importance: 15%
- Effort: 5%
- Dependencies: 10%

Prioritizes tasks based primarily on due dates, suitable for deadline-focused work.

## Final Priority Calculation

The final priority score is calculated as a weighted sum:

```
priority_score = (urgency * w_u) + (importance * w_i) + (effort * w_e) + (dependency * w_d)
```

Where `w_u`, `w_i`, `w_e`, `w_d` are the strategy-specific weights that sum to 1.0.

## Priority Labels

Tasks are categorized into three priority levels based on their final score:

- **HIGH**: score ≥ 80
- **MEDIUM**: 50 ≤ score < 80
- **LOW**: score < 50

## Circular Dependency Detection

The algorithm uses a Depth-First Search (DFS) algorithm to detect circular dependencies in the task graph. This prevents infinite loops and helps users identify problematic dependency chains.

**Algorithm:**
1. Build a reverse dependency graph (which tasks depend on each task)
2. For each task, perform DFS to detect cycles
3. Track visited nodes and recursion stack
4. When a node is encountered in the recursion stack, a cycle is detected
5. Return all detected circular chains

## Edge Case Handling

### Missing Data
- Missing `due_date`: Defaults to 7 days from now
- Missing `due_time`: Defaults to 23:59
- Missing `importance`: Defaults to 5 (medium)
- Missing `estimated_hours`: Defaults to 1.0 hour
- Missing `dependencies`: Defaults to empty array

### Invalid Data
- `importance` outside 1-10: Clamped to valid range
- `estimated_hours` ≤ 0: Rejected or defaulted to 0.1
- Invalid date format: Returns validation error
- Malformed JSON: Returns parsing error

### Overdue Tasks
Overdue tasks receive penalty scoring that increases their priority score, ensuring they are addressed promptly.

## Example Calculation

Consider a task with:
- Due in 2 days (urgency: 94)
- Importance: 8 (importance: 80)
- Estimated 4 hours (effort: 90)
- Blocks 2 tasks (dependency: 50)

Using Smart Balance (Developer) strategy:
```
priority_score = (94 * 0.3) + (80 * 0.3) + (90 * 0.2) + (50 * 0.2)
               = 28.2 + 24 + 18 + 10
               = 80.2
```

Result: **HIGH** priority task (score ≥ 80)

## Conclusion

This multi-factor scoring system provides a flexible and intelligent way to prioritize tasks. By combining multiple dimensions and allowing strategy selection, users can adapt the prioritization to their specific needs and work style. The algorithm balances mathematical rigor with practical usability, ensuring that the most important and urgent work is identified and prioritized appropriately.

