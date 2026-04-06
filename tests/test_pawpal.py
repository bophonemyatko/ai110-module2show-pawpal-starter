import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task(title="Feed Luna", duration_minutes=10, priority="high", preferred_time="08:30", mandatory=True)
    assert task.status == "incomplete"
    task.mark_complete()
    assert task.status == "complete"


def test_add_task_increases_pet_task_count():
    luna = Pet(name="Luna", species="Dog")
    assert len(luna.get_tasks()) == 0
    luna.add_task(Task(title="Morning walk", duration_minutes=30, priority="high", preferred_time="08:00", mandatory=True))
    assert len(luna.get_tasks()) == 1
    luna.add_task(Task(title="Brush Luna", duration_minutes=15, priority="low", preferred_time="11:00", mandatory=False))
    assert len(luna.get_tasks()) == 2
