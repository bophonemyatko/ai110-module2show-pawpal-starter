from __future__ import annotations
from dataclasses import dataclass, field, replace as dc_replace
from datetime import date
from typing import Optional


PRIORITY_RANK = {"high": 1, "medium": 2, "low": 3}
SCHEDULE_START_HOUR = 8   # daily schedule begins at 8:00 AM
TASK_BUFFER_MINUTES = 5   # idle gap inserted between consecutive tasks


def _minutes_to_time(offset_minutes: int) -> str:
    """Convert a minute offset from SCHEDULE_START_HOUR into HH:MM format."""
    total = SCHEDULE_START_HOUR * 60 + offset_minutes
    hours, mins = divmod(total, 60)
    return f"{hours:02d}:{mins:02d}"


def _parse_preferred_time(preferred_time: str) -> Optional[int]:
    """Parse an HH:MM string into total minutes since midnight.
    Returns None if the string is blank or not a valid HH:MM time."""
    if not preferred_time or not preferred_time.strip():
        return None
    try:
        parts = preferred_time.strip().split(":")
        if len(parts) != 2:
            return None
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        return h * 60 + m
    except ValueError:
        return None


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

    def filter_tasks(self, status: Optional[str] = None) -> list[Task]:
        """Return tasks for this pet, optionally filtered by status.
        Pass status='complete', 'incomplete', or 'in progress'."""
        if status is None:
            return self.tasks
        return [t for t in self.tasks if t.status == status]


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    preferred_time: str
    mandatory: bool
    pet: Pet = None
    status: str = "incomplete"            # "incomplete" | "in progress" | "complete"
    last_skipped: Optional[str] = None    # ISO date set when skipped due to time budget
    recurrence: Optional[str] = None      # None | "daily" | "weekly"

    def __post_init__(self):
        """Validate preferred_time format and recurrence value on creation."""
        if self.preferred_time and _parse_preferred_time(self.preferred_time) is None:
            raise ValueError(
                f"Invalid preferred_time '{self.preferred_time}'. "
                "Use HH:MM format (e.g. '08:00')."
            )
        if self.recurrence not in (None, "daily", "weekly"):
            raise ValueError(
                f"Invalid recurrence '{self.recurrence}'. Use 'daily', 'weekly', or None."
            )

    def mark_complete(self) -> None:
        """Mark this task as fully done. Scheduler will skip it.
        If the task recurs daily or weekly, a fresh copy is automatically
        added back to the pet so it reappears in the next scheduled plan."""
        self.status = "complete"
        if self.recurrence in ("daily", "weekly") and self.pet is not None:
            next_task = dc_replace(self, status="incomplete", last_skipped=None)
            self.pet.add_task(next_task)

    def mark_in_progress(self) -> None:
        """Mark this task as actively being worked on."""
        self.status = "in progress"

    def get_priority(self) -> int:
        """Numeric sort rank — lower is higher priority.

        Mandatory tasks always outrank non-mandatory ones. Urgency decay:
        each day a task was skipped due to the time budget reduces its rank by 1
        (floored at 1), so repeatedly deferred tasks gradually bubble up."""
        rank = PRIORITY_RANK.get(self.priority.lower(), 3)
        if not self.mandatory:
            rank += len(PRIORITY_RANK)
        if self.last_skipped:
            try:
                days_skipped = (date.today() - date.fromisoformat(self.last_skipped)).days
                rank = max(1, rank - days_skipped)
            except ValueError:
                pass
        return rank

    def edit_task(self, **kwargs) -> None:
        """Update any task attribute by passing it as a keyword argument.
        Validates preferred_time format if that field is being changed."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == "preferred_time" and value and _parse_preferred_time(value) is None:
                    raise ValueError(
                        f"Invalid preferred_time '{value}'. "
                        "Use HH:MM format (e.g. '08:00')."
                    )
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

    def filter_tasks(self, status: Optional[str] = None, pet_name: Optional[str] = None) -> list[Task]:
        """Return tasks filtered by status, pet name, or both.
        Pass status='complete', 'incomplete', or 'in progress'.
        Pass pet_name to restrict results to a specific pet."""
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet and t.pet.name == pet_name]
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def update_preferences(self, key: str, value) -> None:
        """Add or update a single preference entry."""
        self.preferences[key] = value


class DailyPlanner:
    def __init__(self, owner: Owner, pets: list[Pet]):
        self.owner = owner
        self.pets = pets
        self.scheduled_tasks: list[ScheduledTask] = []
        self.skipped_tasks: list[Task] = []   # tasks dropped due to time budget
        self.total_minutes: int = 0

    def add_scheduled_task(self, scheduled_task: ScheduledTask) -> None:
        """Append a scheduled task to the plan and update the total time used."""
        self.scheduled_tasks.append(scheduled_task)
        self.total_minutes += scheduled_task.task.duration_minutes

    def get_reason(self) -> str:
        """Return a formatted summary of every scheduled task and its reason,
        followed by any tasks that were skipped due to the time budget."""
        if not self.scheduled_tasks:
            return "No tasks scheduled."
        lines = [
            f"- {st.task.title} ({st.start_time}–{st.end_time}): {st.reason}"
            for st in self.scheduled_tasks
        ]
        if self.skipped_tasks:
            lines.append("\nSkipped (did not fit in time budget):")
            for t in self.skipped_tasks:
                lines.append(f"  - {t.title} ({t.duration_minutes} min)")
        return "\n".join(lines)


class Scheduler:
    def generate_plan(self, owner: Owner) -> DailyPlanner:
        """Schedule all pet tasks within the owner's daily free time and return
        a DailyPlanner. Applies preferred-time placement, inter-task buffers,
        round-robin pet fairness, skip_weekends preference, and a bin-packing
        second pass to fill any leftover time."""
        planner = DailyPlanner(owner=owner, pets=owner.pets)
        owner.daily_planner = planner

        # Respect skip_weekends preference (5 = Saturday, 6 = Sunday)
        if owner.preferences.get("skip_weekends", False) and date.today().weekday() >= 5:
            return planner

        remaining_minutes = owner.free_minutes_per_day
        elapsed_minutes = 0
        first_task = True
        skipped: list[Task] = []

        sorted_tasks = self._interleave_by_pet(self.sort_tasks(owner.get_all_tasks()))

        for task in sorted_tasks:
            if task.status == "complete":
                continue

            # Insert a buffer gap after every task except the very first
            buffer = 0 if first_task else TASK_BUFFER_MINUTES

            # Honor preferred_time: idle forward if we haven't reached it yet.
            # When we idle past where the buffer would land, absorb it into the gap.
            pref_minutes = _parse_preferred_time(task.preferred_time)
            if pref_minutes is not None:
                pref_offset = pref_minutes - SCHEDULE_START_HOUR * 60
                if pref_offset > elapsed_minutes + buffer:
                    elapsed_minutes = pref_offset
                    buffer = 0  # idle gap already covers the buffer

            if task.duration_minutes > remaining_minutes:
                task.last_skipped = date.today().isoformat()
                skipped.append(task)
                continue

            start_time = _minutes_to_time(elapsed_minutes + buffer)
            elapsed_minutes += buffer + task.duration_minutes
            end_time = _minutes_to_time(elapsed_minutes)
            remaining_minutes -= task.duration_minutes
            first_task = False

            planner.add_scheduled_task(ScheduledTask(
                task=task,
                start_time=start_time,
                end_time=end_time,
                reason=self.explain_choice(task),
            ))

        # Second pass: bin-packing — fill any remaining budget with the shortest
        # skipped tasks that now fit, sorted shortest-first to maximise coverage.
        if remaining_minutes > 0 and skipped:
            still_skipped: list[Task] = []
            for task in sorted(skipped, key=lambda t: t.duration_minutes):
                buffer = 0 if first_task else TASK_BUFFER_MINUTES
                if task.duration_minutes <= remaining_minutes:
                    task.last_skipped = None  # successfully scheduled; clear skip date
                    start_time = _minutes_to_time(elapsed_minutes + buffer)
                    elapsed_minutes += buffer + task.duration_minutes
                    end_time = _minutes_to_time(elapsed_minutes)
                    remaining_minutes -= task.duration_minutes
                    first_task = False
                    planner.add_scheduled_task(ScheduledTask(
                        task=task,
                        start_time=start_time,
                        end_time=end_time,
                        reason=self.explain_choice(task) + " (fills remaining time)",
                    ))
                else:
                    still_skipped.append(task)
            skipped = still_skipped

        planner.skipped_tasks = skipped
        return planner

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort by priority rank (mandatory first, high → low), then by
        preferred_time so earlier-preferred tasks land earlier in the day,
        then by duration as a final tiebreaker (shorter tasks first)."""
        def sort_key(t: Task):
            pref_minutes = _parse_preferred_time(t.preferred_time)
            pref_sort = pref_minutes if pref_minutes is not None else float("inf")
            return (t.get_priority(), pref_sort, t.duration_minutes)
        return sorted(tasks, key=sort_key)

    def _interleave_by_pet(self, tasks: list[Task]) -> list[Task]:
        """Keep mandatory tasks in their sorted order, then round-robin interleave
        the optional tasks across pets so no single pet monopolises the schedule."""
        mandatory = [t for t in tasks if t.mandatory]
        optional = [t for t in tasks if not t.mandatory]

        pet_queues: dict[str, list[Task]] = {}
        no_pet: list[Task] = []
        for t in optional:
            key = t.pet.name if t.pet else None
            if key is None:
                no_pet.append(t)
            else:
                pet_queues.setdefault(key, []).append(t)

        interleaved: list[Task] = []
        queues = list(pet_queues.values())
        while any(queues):
            for queue in queues:
                if queue:
                    interleaved.append(queue.pop(0))
        interleaved.extend(no_pet)

        return mandatory + interleaved

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
