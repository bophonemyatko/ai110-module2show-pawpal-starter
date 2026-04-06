import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, Task, Owner, Scheduler


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


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_tasks_chronological_by_preferred_time():
    """Tasks with earlier preferred_time must appear first in the sorted output."""
    scheduler = Scheduler()
    early = Task(title="Morning walk", duration_minutes=20, priority="medium",
                 preferred_time="08:00", mandatory=False)
    mid   = Task(title="Midday meal",  duration_minutes=10, priority="medium",
                 preferred_time="12:00", mandatory=False)
    late  = Task(title="Evening brush", duration_minutes=15, priority="medium",
                 preferred_time="18:00", mandatory=False)

    # Pass in reverse order to confirm sorting is applied
    result = scheduler.sort_tasks([late, mid, early])
    times = [t.preferred_time for t in result]
    assert times == ["08:00", "12:00", "18:00"]


def test_sort_tasks_no_preferred_time_sorts_last():
    """Tasks without a preferred_time should come after those that have one."""
    scheduler = Scheduler()
    with_time    = Task(title="Walk",  duration_minutes=20, priority="medium",
                        preferred_time="09:00", mandatory=False)
    without_time = Task(title="Brush", duration_minutes=10, priority="medium",
                        preferred_time="",      mandatory=False)

    result = scheduler.sort_tasks([without_time, with_time])
    assert result[0].title == "Walk"
    assert result[1].title == "Brush"


def test_sort_tasks_mandatory_before_optional():
    """Mandatory tasks must outrank optional tasks regardless of priority label."""
    scheduler = Scheduler()
    optional_high = Task(title="Play",   duration_minutes=15, priority="high",
                         preferred_time="", mandatory=False)
    mandatory_low  = Task(title="Meds",  duration_minutes=5,  priority="low",
                          preferred_time="", mandatory=True)

    result = scheduler.sort_tasks([optional_high, mandatory_low])
    assert result[0].title == "Meds"


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_recurrence_spawns_new_task_on_complete():
    """Completing a daily task must add exactly one new incomplete copy to the pet."""
    luna = Pet(name="Luna", species="Dog")
    feed = Task(title="Feed Luna", duration_minutes=10, priority="high",
                preferred_time="08:00", mandatory=True, recurrence="daily")
    luna.add_task(feed)

    assert len(luna.get_tasks()) == 1
    feed.mark_complete()

    tasks = luna.get_tasks()
    assert len(tasks) == 2                              # original + spawned copy
    assert tasks[0].status == "complete"
    new_task = tasks[1]
    assert new_task.status == "incomplete"
    assert new_task.recurrence == "daily"
    assert new_task.last_skipped is None               # fresh copy, no stale skip date


def test_non_recurring_task_does_not_spawn():
    """Completing a non-recurring task must NOT add any new task to the pet."""
    luna = Pet(name="Luna", species="Dog")
    brush = Task(title="Brush Luna", duration_minutes=15, priority="low",
                 preferred_time="", mandatory=False, recurrence=None)
    luna.add_task(brush)

    brush.mark_complete()
    assert len(luna.get_tasks()) == 1                  # still just the one completed task


def test_recurring_task_without_pet_does_not_crash():
    """A recurring task that has no pet assigned must complete without raising."""
    orphan = Task(title="Generic task", duration_minutes=5, priority="medium",
                  preferred_time="", mandatory=False, recurrence="daily")
    orphan.mark_complete()                             # should not raise
    assert orphan.status == "complete"


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_warns_on_duplicate_preferred_time():
    """Two tasks sharing the same preferred_time must produce a conflict warning."""
    luna  = Pet(name="Luna",  species="Dog")
    mochi = Pet(name="Mochi", species="Cat")

    task_a = Task(title="Walk Luna",   duration_minutes=20, priority="high",
                  preferred_time="09:00", mandatory=True)
    task_b = Task(title="Feed Mochi",  duration_minutes=10, priority="high",
                  preferred_time="09:00", mandatory=True)
    luna.add_task(task_a)
    mochi.add_task(task_b)

    owner = Owner(name="Alex", free_minutes_per_day=120, preferences={})
    owner.add_pet(luna)
    owner.add_pet(mochi)

    planner = Scheduler().generate_plan(owner)
    assert any("09:00" in w for w in planner.warnings)


def test_no_conflict_warning_for_unique_preferred_times():
    """Tasks with different preferred_times must not generate any conflict warning."""
    luna = Pet(name="Luna", species="Dog")
    luna.add_task(Task(title="Walk",  duration_minutes=20, priority="high",
                       preferred_time="08:00", mandatory=True))
    luna.add_task(Task(title="Brush", duration_minutes=10, priority="low",
                       preferred_time="11:00", mandatory=False))

    owner = Owner(name="Alex", free_minutes_per_day=120, preferences={})
    owner.add_pet(luna)

    planner = Scheduler().generate_plan(owner)
    conflict_warnings = [w for w in planner.warnings if "conflict" in w.lower()]
    assert len(conflict_warnings) == 0
