"""
Task Manager — In-memory CRUD task manager.
See SPEC.md for full specification.
"""

from datetime import datetime, timezone


class TaskManager:
    def __init__(self):
        self._tasks = {}
        self._next_id = 1

    def create_task(self, title, description="", priority="medium"):
        """Create a new task and return it."""
        # BUG: Missing title length validation (SPEC says max 100 chars)
        if not title:
            raise ValueError("Title cannot be empty")

        valid_priorities = ("low", "medium", "high")
        if priority not in valid_priorities:
            raise ValueError(f"Priority must be one of {valid_priorities}")

        task = {
            "id": self._next_id,
            "title": title,
            "description": description,
            "status": "todo",
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def get_task(self, task_id):
        """Return a task by ID."""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")
        return self._tasks[task_id]

    def list_tasks(self, status=None):
        """Return all tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        # BUG: Not sorted by id (SPEC requires sorted by id ascending)
        return tasks

    def update_task(self, task_id, **kwargs):
        """Update fields of an existing task."""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")

        allowed_fields = {"title", "description", "status", "priority"}
        for key in kwargs:
            if key not in allowed_fields:
                raise ValueError(f"Cannot update field: {key}")

        task = self._tasks[task_id]

        if "title" in kwargs:
            if not kwargs["title"]:
                raise ValueError("Title cannot be empty")
            # BUG: Missing max length check for title
            task["title"] = kwargs["title"]

        if "description" in kwargs:
            task["description"] = kwargs["description"]

        if "status" in kwargs:
            valid_statuses = ("todo", "in_progress", "done")
            if kwargs["status"] not in valid_statuses:
                raise ValueError(f"Status must be one of {valid_statuses}")
            task["status"] = kwargs["status"]

        if "priority" in kwargs:
            valid_priorities = ("low", "medium", "high")
            if kwargs["priority"] not in valid_priorities:
                raise ValueError(f"Priority must be one of {valid_priorities}")
            task["priority"] = kwargs["priority"]

        return task

    def delete_task(self, task_id):
        """Delete and return a task."""
        if task_id not in self._tasks:
            raise KeyError(f"Task {task_id} not found")
        return self._tasks.pop(task_id)

    def get_stats(self):
        """Return task statistics."""
        # BUG: Missing "in_progress" from by_status when count is 0
        stats = {"total": len(self._tasks), "by_status": {}}
        for task in self._tasks.values():
            s = task["status"]
            stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
        return stats
