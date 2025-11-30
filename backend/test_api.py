"""
Quick API test script to verify endpoints are working.
Run this after starting the Django server.
"""
import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000/api"

def test_analyze_endpoint():
    """Test the analyze endpoint."""
    print("=" * 60)
    print("Testing POST /api/tasks/analyze/")
    print("=" * 60)
    
    # Create test tasks with various scenarios
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    test_tasks = [
        {
            "id": "task_1",
            "title": "Overdue Critical Task",
            "due_date": yesterday,
            "due_time": "17:00",
            "estimated_hours": 8.0,
            "importance": 9,
            "dependencies": [],
            "role": "developer"
        },
        {
            "id": "task_2",
            "title": "Quick Win Task",
            "due_date": tomorrow,
            "due_time": "17:00",
            "estimated_hours": 2.0,
            "importance": 5,
            "dependencies": ["task_1"],
            "role": "developer"
        },
        {
            "id": "task_3",
            "title": "High Importance Future Task",
            "due_date": (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            "due_time": "17:00",
            "estimated_hours": 10.0,
            "importance": 8,
            "dependencies": [],
            "role": "developer"
        }
    ]
    
    try:
        response = requests.post(
            f"{API_BASE}/tasks/analyze/",
            json={
                "tasks": test_tasks,
                "strategy": "smart_balance",
                "role": "developer"
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! Analyzed {len(data['tasks'])} tasks")
            print(f"Warnings: {len(data.get('warnings', []))}")
            print(f"Circular Dependencies: {len(data.get('circular_dependencies', []))}")
            
            print("\nTop 3 Tasks:")
            for i, task in enumerate(data['tasks'][:3], 1):
                print(f"\n{i}. {task['title']}")
                print(f"   Priority: {task['priority_label']} ({task['priority_score']:.1f})")
                print(f"   Overdue: {task.get('is_overdue', False)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the Django server is running!")
        print("   Run: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_suggest_endpoint():
    """Test the suggest endpoint."""
    print("\n" + "=" * 60)
    print("Testing POST /api/tasks/suggest/")
    print("=" * 60)
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    test_tasks = [
        {
            "title": "Task 1",
            "due_date": tomorrow,
            "due_time": "17:00",
            "estimated_hours": 8.0,
            "importance": 7,
            "dependencies": [],
            "role": "developer"
        },
        {
            "title": "Task 2",
            "due_date": (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            "due_time": "15:00",
            "estimated_hours": 4.0,
            "importance": 9,
            "dependencies": [],
            "role": "developer"
        },
        {
            "title": "Task 3",
            "due_date": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            "due_time": "12:00",
            "estimated_hours": 2.0,
            "importance": 6,
            "dependencies": [],
            "role": "developer"
        },
        {
            "title": "Task 4",
            "due_date": (datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d'),
            "due_time": "10:00",
            "estimated_hours": 6.0,
            "importance": 8,
            "dependencies": [],
            "role": "developer"
        }
    ]
    
    try:
        response = requests.post(
            f"{API_BASE}/tasks/suggest/",
            json={
                "tasks": test_tasks,
                "strategy": "fastest_wins"
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success! Got {len(data['suggestions'])} suggestions")
            print(f"Strategy: {data['strategy']}")
            print(f"Total Tasks: {data['total_tasks']}")
            
            print("\nTop 3 Suggestions:")
            for i, task in enumerate(data['suggestions'], 1):
                print(f"\n{i}. {task['title']}")
                print(f"   Priority: {task['priority_label']} ({task['priority_score']:.1f})")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the Django server is running!")
        print("   Run: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_circular_dependency_detection():
    """Test circular dependency detection."""
    print("\n" + "=" * 60)
    print("Testing Circular Dependency Detection")
    print("=" * 60)
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Create circular dependency: task_1 -> task_2 -> task_1
    test_tasks = [
        {
            "id": "task_1",
            "title": "Task 1",
            "due_date": tomorrow,
            "due_time": "17:00",
            "estimated_hours": 5.0,
            "importance": 5,
            "dependencies": ["task_2"],  # Depends on task_2
            "role": "developer"
        },
        {
            "id": "task_2",
            "title": "Task 2",
            "due_date": tomorrow,
            "due_time": "17:00",
            "estimated_hours": 5.0,
            "importance": 5,
            "dependencies": ["task_1"],  # Depends on task_1 (circular!)
            "role": "developer"
        }
    ]
    
    try:
        response = requests.post(
            f"{API_BASE}/tasks/analyze/",
            json={
                "tasks": test_tasks,
                "strategy": "smart_balance"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            circular_deps = data.get('circular_dependencies', [])
            
            if circular_deps:
                print(f"✅ Circular dependency detected!")
                print(f"Found {len(circular_deps)} circular chain(s):")
                for chain in circular_deps:
                    print(f"   - {chain}")
            else:
                print("⚠️  No circular dependencies detected (unexpected for this test)")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Smart Task Analyzer - API Test Suite")
    print("=" * 60)
    print("\nMake sure the Django server is running:")
    print("  python manage.py runserver\n")
    
    test_analyze_endpoint()
    test_suggest_endpoint()
    test_circular_dependency_detection()
    
    print("\n" + "=" * 60)
    print("Test Suite Complete!")
    print("=" * 60)

