from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


PRIORITY_RANK = {"high": 1, "medium": 2, "low": 3}
SCHEDULE_START_HOUR = 8  # daily schedule begins at 8:00 AM


def _minutes_to_time(offset_minutes: int) -> str:
    """Convert a minute offset from SCHEDULE_START_HOUR into HH:MM format."""
    total = SCHEDULE_START_HOUR * 60 + offset_minutes
    hours, mins = divmod(total, 60)
    return f"{hours:02d}:{mins:02d}"


@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and set the back-reference on the task."""
        task.pet = self
        self.tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks belonging to this pet."""
        return self.tasks


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    preferred_time: str
    mandatory: bool
    pet: Pet = None
    status: str = "incomplete"  # "incomplete" | "in progress" | "complete"

    def mark_complete(self) -> None:
        """Mark this task as fully done. Scheduler will skip it."""
        self.status = "complete"

    def mark_in_progress(self) -> None:
        """Mark this task as actively being worked on."""
        self.status = "in progress"

    def get_priority(self) -> int:
        """Numeric sort rank — lower is higher priority.
        Mandatory tasks always rank above non-mandatory ones."""
        rank = PRIORITY_RANK.get(self.priority.lower(), 3)
        return rank if self.mandatory else rank + len(PRIORITY_RANK)

    def edit_task(self, **kwargs) -> None:
        """Update any task attribute by passing it as a keyword argument."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


@dataclass
class ScheduledTask:
    task: Task
    start_time: str
    end_time: str
    reason: str


class Owner:
    def __init__(self, name: str, free_minutes_per_day: int, preferences: dict):
        self.name = name
        self.free_minutes_per_day = free_minutes_per_day
        self.preferences = preferences
        self.pets: list[Pet] = []
        self.daily_planner: Optional[DailyPlanner] = None

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Collect and return all tasks across every pet."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def update_preferences(self, key: str, value) -> None:
        """Add or update a single preference entry."""
        self.preferences[key] = value


class DailyPlanner:
    def __init__(self, owner: Owner, pets: list[Pet]):
        self.owner = owner
        self.pets = pets
        self.scheduled_tasks: list[ScheduledTask] = []
        self.total_minutes: int = 0

    def add_scheduled_task(self, scheduled_task: ScheduledTask) -> None:
        """Append a scheduled task to the plan and update the total time used."""
        self.scheduled_tasks.append(scheduled_task)
        self.total_minutes += scheduled_task.task.duration_minutes

    def get_reason(self) -> str:
        """Return a formatted summary of every scheduled task and its reason."""
        if not self.scheduled_tasks:
            return "No tasks scheduled."
        lines = [
            f"- {st.task.title} ({st.start_time}–{st.end_time}): {st.reason}"
            for st in self.scheduled_tasks
        ]
        return "\n".join(lines)


class Scheduler:
    def generate_plan(self, owner: Owner) -> DailyPlanner:
        """Retrieve all tasks from the owner's pets, schedule them within the
        owner's free time, and return a DailyPlanner."""
        planner = DailyPlanner(owner=owner, pets=owner.pets)
        owner.daily_planner = planner

        remaining_minutes = owner.free_minutes_per_day
        elapsed_minutes = 0

        for task in self.sort_tasks(owner.get_all_tasks()):
            if task.status == "complete" or task.duration_minutes > remaining_minutes:
                continue

            start_time = _minutes_to_time(elapsed_minutes)
            elapsed_minutes += task.duration_minutes
            end_time = _minutes_to_time(elapsed_minutes)
            remaining_minutes -= task.duration_minutes

            planner.add_scheduled_task(ScheduledTask(
                task=task,
                start_time=start_time,
                end_time=end_time,
                reason=self.explain_choice(task),
            ))

        return planner

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort by priority rank (mandatory first, high → low),
        then by duration as a tiebreaker (shorter tasks first)."""
        return sorted(tasks, key=lambda t: (t.get_priority(), t.duration_minutes))

    def explain_choice(self, task: Task) -> str:
        """Build a human-readable sentence explaining why this task was scheduled."""
        parts = []
        if task.mandatory:
            parts.append("mandatory task")
        parts.append(f"{task.priority} priority")
        if task.preferred_time:
            parts.append(f"preferred at {task.preferred_time}")
        if task.pet:
            parts.append(f"for {task.pet.name}")
        return ", ".join(parts).capitalize() + "."
