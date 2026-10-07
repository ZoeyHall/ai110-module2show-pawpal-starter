"""PawPal+ core classes: Owner, Pet, Task, and Scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

PRIORITY_VALUES = {"high": 3, "medium": 2, "low": 1}
FREQUENCY_DAYS = {"daily": 1, "weekly": 7, "once": None}


def time_to_minutes(time: str) -> int | None:
    """Convert a clock time to minutes after midnight.

    Comparing whole numbers instead of strings means "7:30" correctly sorts
    before "10:00", with or without a leading zero.

    Args:
        time: A time written as "H:MM" or "HH:MM" (24-hour clock).

    Returns:
        Minutes after midnight (0-1439), or None if the time is empty, not in
        H:MM form, or out of range (such as "25:00"). It never raises, so
        callers can treat a bad time as "no time" instead of crashing.
    """
    try:
        hours, minutes = map(int, time.split(":"))
    except ValueError:
        return None
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        return None
    return hours * 60 + minutes


def format_minutes(total: int) -> str:
    """Format minutes after midnight as a zero-padded "HH:MM" string."""
    return f"{total // 60:02d}:{total % 60:02d}"


@dataclass
class Task:
    """A single pet care activity, such as a walk, feeding, or medication."""

    description: str
    duration_minutes: int
    priority: str = "medium"  # "high", "medium", or "low"
    time: str = ""  # preferred time as "HH:MM", or "" for any time
    frequency: str = "daily"  # "daily", "weekly", or "once"
    completed: bool = False
    pet_name: str = ""  # filled in when the task is added to a pet
    due_date: date = field(default_factory=date.today)

    def __post_init__(self) -> None:
        """Normalize priority/frequency and reject invalid values."""
        self.priority = self.priority.lower()
        if self.priority not in PRIORITY_VALUES:
            raise ValueError(f"priority must be one of {list(PRIORITY_VALUES)}")
        self.frequency = self.frequency.lower()
        if self.frequency not in FREQUENCY_DAYS:
            raise ValueError(f"frequency must be one of {list(FREQUENCY_DAYS)}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0")

    def priority_value(self) -> int:
        """Return a numeric value for priority so tasks can be sorted."""
        return PRIORITY_VALUES[self.priority]

    def mark_complete(self) -> Task | None:
        """Mark this task as done and build its next occurrence, if it repeats.

        The next occurrence is a copy of this task with completed=False and a
        due date counted from this task's due date (not from today): +1 day for
        "daily" and +7 days for "weekly". A task finished late therefore comes
        back already overdue, so missed days are not silently skipped.

        Completing a task that is already completed does nothing, so calling
        this twice never creates a duplicate next occurrence.

        This method does not add the new task to a pet; use
        Scheduler.mark_task_complete() for that.

        Returns:
            The next Task for "daily" or "weekly" tasks, or None for "once"
            tasks and for tasks that were already completed.
        """
        if self.completed:
            return None
        self.completed = True
        interval = FREQUENCY_DAYS[self.frequency]
        if interval is None:
            return None
        return replace(
            self, completed=False, due_date=self.due_date + timedelta(days=interval)
        )


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, description: str) -> None:
        """Remove pending tasks with the given description.

        Completed tasks are kept as history, so removing a recurring task
        deletes its upcoming occurrences without erasing what was already done.
        """
        self.tasks = [
            t for t in self.tasks if t.completed or t.description != description
        ]

    def pending_tasks(self) -> list[Task]:
        """Return the tasks that are not completed yet."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    """A pet owner, their available time, and their pets."""

    name: str
    available_minutes: int
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds a daily care plan that fits within the owner's available time."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler for the given owner with an empty plan."""
        self.owner = owner
        self.scheduled: list[Task] = []
        self.skipped: list[Task] = []
        self.conflicts: list[str] = []

    def get_pending_tasks(self, on_date: date | None = None) -> list[Task]:
        """Return incomplete tasks that are due on or before a given date.

        Including earlier dates means overdue tasks stay visible, while future
        occurrences created by recurring tasks are left out of today's plan.

        Args:
            on_date: The day to plan for. Defaults to today.

        Returns:
            Incomplete tasks across all pets with due_date <= on_date.
        """
        on_date = on_date or date.today()
        return [
            t
            for t in self.owner.get_all_tasks()
            if not t.completed and t.due_date <= on_date
        ]

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task and add its next occurrence to the same pet.

        This is the method the app should call when the owner checks off a
        task, so recurring tasks are never lost.

        Args:
            task: A task belonging to one of this owner's pets.

        Returns:
            The newly added next occurrence, or None for one-time tasks,
            tasks that were already completed, or if the task's pet can't be
            found.
        """
        next_task = task.mark_complete()
        pet = self.owner.get_pet(task.pet_name)
        if next_task is not None and pet is not None:
            pet.add_task(next_task)
        return next_task

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[Task]:
        """Return tasks matching a pet name and/or completion status.

        Each filter is optional: None means "don't filter on this", so
        filter_tasks() returns every task and filter_tasks(completed=False)
        returns pending tasks for all pets. Runs in a single pass over the
        owner's tasks.

        Args:
            pet_name: Only include this pet's tasks. None includes all pets.
            completed: True for finished tasks, False for pending tasks, or
                None for both.

        Returns:
            Matching tasks, in the order they appear on each pet.
        """
        return [
            t
            for t in self.owner.get_all_tasks()
            if (pet_name is None or t.pet_name == pet_name)
            and (completed is None or t.completed == completed)
        ]

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by priority (highest first), then shortest first.

        Putting short tasks first among equal priorities lets the greedy
        planner in generate_plan() fit more tasks into the available time.
        """
        return sorted(tasks, key=lambda t: (-t.priority_value(), t.duration_minutes))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks in order of their start time.

        Times are compared as minutes after midnight (see time_to_minutes), so
        "7:30" and "07:30" sort the same way. Tasks with no time, or a time
        that can't be read, go last. The sort is stable, so tasks with the same
        time keep their incoming order (in generate_plan, that is priority).

        Args:
            tasks: The tasks to sort. The list is not modified.

        Returns:
            A new list sorted by time.
        """

        def time_key(task: Task) -> tuple[int, int]:
            start = time_to_minutes(task.time)
            return (1, 0) if start is None else (0, start)

        return sorted(tasks, key=time_key)

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Find timed tasks whose time slots overlap and describe them as warnings.

        Each task occupies the slot [start, start + duration), so tasks that
        are back to back (one ends at 08:00, the next starts at 08:00) do not
        conflict. Conflicts are reported for the same pet and across pets.

        Algorithm: sort the slots by start time, then compare each task with
        the tasks after it, stopping as soon as a later task starts at or after
        the current task ends. Every overlapping pair is found, including a
        long task that overlaps several short ones.

        This is a lightweight check: it never raises. Tasks without a time are
        ignored, and a task with an unreadable time gets its own warning.

        Args:
            tasks: The tasks to check, usually the current plan.

        Returns:
            One warning string per overlapping pair or unreadable time, or an
            empty list if everything fits.
        """
        warnings: list[str] = []
        timed: list[tuple[int, int, Task]] = []
        for task in tasks:
            if not task.time:
                continue
            start = time_to_minutes(task.time)
            if start is None:
                warnings.append(
                    f"Warning: {task.pet_name}'s '{task.description}' has an "
                    f"unreadable time '{task.time}' and was not checked."
                )
                continue
            timed.append((start, start + task.duration_minutes, task))

        timed.sort(key=lambda item: item[0])
        for i, (start_a, end_a, a) in enumerate(timed):
            for start_b, end_b, b in timed[i + 1 :]:
                if start_b >= end_a:
                    break
                who = (
                    f"for {a.pet_name}"
                    if a.pet_name == b.pet_name
                    else f"for {a.pet_name} and {b.pet_name}"
                )
                warnings.append(
                    f"Warning: '{a.description}' ({format_minutes(start_a)}-"
                    f"{format_minutes(end_a)}) overlaps '{b.description}' "
                    f"({format_minutes(start_b)}-{format_minutes(end_b)}) {who}."
                )
        return warnings

    def generate_plan(self) -> list[Task]:
        """Choose which of today's tasks fit in the owner's time and order them.

        Steps:
            1. Take pending tasks due today or earlier (get_pending_tasks).
            2. Greedily add them in priority order (sort_tasks) while they fit
               in owner.available_minutes; the rest go into self.skipped.
            3. Sort the chosen tasks by time (sort_by_time).
            4. Check the plan for overlaps and store warnings in
               self.conflicts (detect_conflicts).

        Returns:
            The scheduled tasks in time order (also stored in self.scheduled).
        """
        self.scheduled = []
        self.skipped = []
        minutes_left = self.owner.available_minutes

        for task in self.sort_tasks(self.get_pending_tasks()):
            if task.duration_minutes <= minutes_left:
                self.scheduled.append(task)
                minutes_left -= task.duration_minutes
            else:
                self.skipped.append(task)

        self.scheduled = self.sort_by_time(self.scheduled)
        self.conflicts = self.detect_conflicts(self.scheduled)
        return self.scheduled

    def total_scheduled_minutes(self) -> int:
        """Return the total minutes used by the current plan."""
        return sum(t.duration_minutes for t in self.scheduled)

    def explain_plan(self) -> str:
        """Return a readable explanation of why tasks were scheduled or skipped."""
        if not self.scheduled and not self.skipped:
            return "No pending tasks to schedule."

        lines = [
            f"Plan for {self.owner.name}: {self.total_scheduled_minutes()} of "
            f"{self.owner.available_minutes} minutes used."
        ]
        for task in self.scheduled:
            when = task.time or "any time"
            lines.append(
                f"- {when}: {task.description} for {task.pet_name} "
                f"({task.duration_minutes} min, {task.priority} priority)"
            )
        if self.skipped:
            lines.append("Skipped (not enough time left):")
            for task in self.skipped:
                lines.append(
                    f"- {task.description} for {task.pet_name} "
                    f"({task.duration_minutes} min, {task.priority} priority)"
                )
        lines.extend(self.conflicts)
        return "\n".join(lines)
