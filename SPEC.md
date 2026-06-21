# Task Manager API — Specification

## Overview
A simple in-memory task manager with CRUD operations.

## Data Model

Each task has:
- `id` (int): Auto-incrementing unique identifier
- `title` (str): Required, non-empty, max 100 characters
- `description` (str): Optional, max 500 characters
- `status` (str): One of "todo", "in_progress", "done". Default: "todo"
- `priority` (str): One of "low", "medium", "high". Default: "medium"
- `created_at` (str): ISO 8601 timestamp, set automatically on creation

## Functions

### `create_task(title, description="", priority="medium") -> dict`
- Creates a new task and returns it
- Must validate: title is non-empty and <= 100 chars
- Must validate: priority is one of "low", "medium", "high"
- Must raise `ValueError` for invalid inputs
- Must auto-assign an incrementing `id` starting from 1
- Must set `status` to "todo"
- Must set `created_at` to current UTC time in ISO format

### `get_task(task_id) -> dict`
- Returns the task with the given ID
- Must raise `KeyError` if task not found

### `list_tasks(status=None) -> list[dict]`
- Returns all tasks
- If `status` is provided, filter to only tasks with that status
- Must return tasks sorted by `id` ascending

### `update_task(task_id, **kwargs) -> dict`
- Updates the specified fields of a task
- Only `title`, `description`, `status`, and `priority` can be updated
- Must validate same rules as `create_task` for title and priority
- Must validate status is one of "todo", "in_progress", "done"
- Must raise `KeyError` if task not found
- Must raise `ValueError` for invalid field names or values
- Returns the updated task

### `delete_task(task_id) -> dict`
- Removes and returns the task
- Must raise `KeyError` if task not found

### `get_stats() -> dict`
- Returns `{"total": int, "by_status": {"todo": int, "in_progress": int, "done": int}}`
- Counts must reflect current state of all tasks

## Error Handling
- All functions must raise appropriate Python exceptions (ValueError, KeyError)
- No silent failures — every invalid input must be caught and reported

## Testing Requirements
- Unit tests must cover all functions
- Must test both valid inputs and error cases (invalid title, unknown ID, etc.)
- Must achieve >= 90% code coverage
