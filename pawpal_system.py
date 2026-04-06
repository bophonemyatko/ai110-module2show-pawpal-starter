from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Pet:
    name: str
    species: str


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str
    preferred_time: str
    mandatory: bool

    def get_priority(self) -> str:
        pass

    def edit_task(self) -> None:
        pass

    def add_task(self) -> None:
        pass


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

    def update_preferences(self) -> None:
        pass


class DailyPlanner:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.scheduled_tasks: list[ScheduledTask] = []
        self.total_minutes: int = 0

    def add_scheduled_task(self) -> None:
        pass

    def get_reason(self) -> str:
        pass


class Scheduler:
    def generate_plan(self, owner: Owner, pet: Pet, tasks: list[Task]) -> DailyPlanner:
        pass

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        pass

    def explain_choice(self, task: Task) -> str:
        pass
