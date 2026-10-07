"""PawPal+ core classes: Owner, Pet, Task, and Scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care activity, such as a walk, feeding, or medication."""

    name: str
    duration_minutes: int
    priority: str  # "high", "medium", or "low"
    category: str = "general"
    completed: bool = False

    def priority_value(self) -> int:
        """Return a numeric value for priority so tasks can be sorted."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def remove_task(self, name: str) -> None:
        """Remove the task with the given name."""
        pass


@dataclass
class Owner:
    """A pet owner, their available time, and their pets."""

    name: str
    available_minutes: int
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass


class Scheduler:
    """Builds a daily care plan that fits within the owner's available time."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.scheduled: list[Task] = []
        self.skipped: list[Task] = []

    def generate_plan(self) -> list[Task]:
        """Choose which tasks fit in today's plan and return them in order."""
        pass

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by priority, then by shorter duration."""
        pass

    def explain_plan(self) -> str:
        """Return a readable explanation of why tasks were scheduled or skipped."""
        pass
