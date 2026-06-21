"""Tests for TaskManager."""

import pytest
from task_manager import TaskManager


@pytest.fixture
def tm():
    return TaskManager()


# --- create_task ---

def test_create_task_basic(tm):
    task = tm.create_task("Buy groceries")
    assert task["title"] == "Buy groceries"
    assert task["status"] == "todo"
    assert task["priority"] == "medium"
    assert task["id"] == 1
    assert "created_at" in task


def test_create_task_with_priority(tm):
    task = tm.create_task("Urgent fix", priority="high")
    assert task["priority"] == "high"


def test_create_task_empty_title(tm):
    with pytest.raises(ValueError):
        tm.create_task("")


def test_create_task_invalid_priority(tm):
    with pytest.raises(ValueError):
        tm.create_task("Test", priority="urgent")


def test_create_task_auto_increment_id(tm):
    t1 = tm.create_task("First")
    t2 = tm.create_task("Second")
    assert t1["id"] == 1
    assert t2["id"] == 2


# --- get_task ---

def test_get_task(tm):
    created = tm.create_task("Test")
    fetched = tm.get_task(created["id"])
    assert fetched["title"] == "Test"


def test_get_task_not_found(tm):
    with pytest.raises(KeyError):
        tm.get_task(999)


# --- list_tasks ---

def test_list_tasks_all(tm):
    tm.create_task("A")
    tm.create_task("B")
    tasks = tm.list_tasks()
    assert len(tasks) == 2


def test_list_tasks_filter_status(tm):
    tm.create_task("A")
    t2 = tm.create_task("B")
    tm.update_task(t2["id"], status="done")
    assert len(tm.list_tasks(status="todo")) == 1
    assert len(tm.list_tasks(status="done")) == 1


# --- update_task ---

def test_update_task_title(tm):
    t = tm.create_task("Old")
    updated = tm.update_task(t["id"], title="New")
    assert updated["title"] == "New"


def test_update_task_status(tm):
    t = tm.create_task("Test")
    updated = tm.update_task(t["id"], status="in_progress")
    assert updated["status"] == "in_progress"


def test_update_task_invalid_field(tm):
    t = tm.create_task("Test")
    with pytest.raises(ValueError):
        tm.update_task(t["id"], color="red")


def test_update_task_not_found(tm):
    with pytest.raises(KeyError):
        tm.update_task(999, title="X")


def test_update_task_invalid_status(tm):
    t = tm.create_task("Test")
    with pytest.raises(ValueError):
        tm.update_task(t["id"], status="archived")


# --- delete_task ---

def test_delete_task(tm):
    t = tm.create_task("Delete me")
    deleted = tm.delete_task(t["id"])
    assert deleted["title"] == "Delete me"
    assert len(tm.list_tasks()) == 0


def test_delete_task_not_found(tm):
    with pytest.raises(KeyError):
        tm.delete_task(999)


# --- get_stats ---

def test_get_stats(tm):
    tm.create_task("A")
    tm.create_task("B")
    tm.update_task(2, status="done")
    stats = tm.get_stats()
    assert stats["total"] == 2
