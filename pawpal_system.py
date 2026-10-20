"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from itertools import combinations

PRIORITIES = ("High", "Medium", "Low")
FREQUENCIES = ("Once", "Daily", "Weekly")
PRIORITY_RANKS = {"High": 3, "Medium": 2, "Low": 1}


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, appointment, etc.)."""

    title: str
    category: str                  # walk / feeding / meds / grooming / appointment / other
    duration_minutes: int
    priority: str                  # one of PRIORITIES
    due_date: date                 # Once: the day it happens; Daily/Weekly: first occurrence
    frequency: str = "Once"        # one of FREQUENCIES
    start_time: time | None = None # only for fixed-time tasks like appointments
    pet_name: str = ""             # set by Pet.add_task so lists can show whose task it is
    completed_dates: list[date] = field(default_factory=list)
    skipped_dates: list[date] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Reject priority/frequency values that aren't in PRIORITIES/FREQUENCIES."""
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {PRIORITIES}, got {self.priority!r}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {FREQUENCIES}, got {self.frequency!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0")

    def mark_complete(self, day: date) -> None:
        """Mark this task as done on the given day (other days of a recurring task stay open)."""
        if day not in self.completed_dates:
            self.completed_dates.append(day)

    def is_completed_on(self, day: date) -> bool:
        """Return True if this task was marked done on the given day."""
        return day in self.completed_dates

    def priority_rank(self) -> int:
        """Return a sortable number for priority: High=3, Medium=2, Low=1."""
        return PRIORITY_RANKS[self.priority]

    def occurs_on(self, day: date) -> bool:
        """Return True if this task happens on the given day (based on frequency and skipped_dates)."""
        if day in self.skipped_dates or day < self.due_date:
            return False
        if self.frequency == "Once":
            return day == self.due_date
        if self.frequency == "Daily":
            return True
        return (day - self.due_date).days % 7 == 0  # Weekly: same weekday as due_date


@dataclass
class Pet:
    """A pet and its list of care tasks."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and set its pet_name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove this exact task (titles aren't unique, e.g. after a reschedule)."""
        self.tasks = [t for t in self.tasks if t is not task]

    def get_tasks(self) -> list[Task]:
        """Return all of this pet's tasks."""
        return list(self.tasks)

    def reschedule_task(self, task: Task, from_date: date, new_date: date) -> None:
        """Move one occurrence of task from from_date to new_date.

        Once tasks: change due_date.
        Daily/Weekly tasks: add from_date to skipped_dates and add a new Once copy on new_date.
        """
        if not any(t is task for t in self.tasks):
            raise ValueError(f"{task.title!r} is not one of {self.name}'s tasks")
        if not task.occurs_on(from_date):
            raise ValueError(f"{task.title!r} does not occur on {from_date}")

        if task.frequency == "Once":
            task.due_date = new_date
        else:
            task.skipped_dates.append(from_date)
            self.add_task(replace(task, due_date=new_date, frequency="Once",
                                  completed_dates=[], skipped_dates=[]))


@dataclass
class Owner:
    """The app user, who owns one or more pets."""

    name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Collect the tasks from every pet into one list."""
        return [task for pet in self.pets for task in pet.get_tasks()]


class Scheduler:
    """Organizes an owner's tasks into daily lists and weekly calendars."""

    def __init__(self, owner: Owner):
        """Create a scheduler that reads tasks from every pet of this owner."""
        self.owner = owner

    def get_daily_tasks(self, day: date) -> list[Task]:
        """Return tasks that occur on day, sorted High -> Medium -> Low.

        Within the same priority, fixed-time tasks come first in time order.
        """
        tasks = [t for t in self.owner.get_all_tasks() if t.occurs_on(day)]
        return sorted(tasks, key=lambda t: (-t.priority_rank(),
                                            t.start_time is None,
                                            t.start_time or time.min))

    def get_weekly_calendar(self, start_day: date) -> dict[date, list[Task]]:
        """Return 7 days starting at start_day, each mapped to its sorted tasks."""
        days = (start_day + timedelta(days=i) for i in range(7))
        return {day: self.get_daily_tasks(day) for day in days}

    def total_duration(self, day: date) -> int:
        """Return the total minutes of all tasks on day."""
        return sum(t.duration_minutes for t in self.get_daily_tasks(day))

    def detect_conflicts(self, day: date) -> list[tuple[Task, Task]]:
        """Return pairs of fixed-time tasks on day whose times overlap."""
        def minutes(t: time) -> int:
            """Convert a time of day to minutes since midnight."""
            return t.hour * 60 + t.minute

        timed = [t for t in self.get_daily_tasks(day) if t.start_time is not None]
        conflicts = []
        for a, b in combinations(timed, 2):
            a_start, b_start = minutes(a.start_time), minutes(b.start_time)
            if a_start < b_start + b.duration_minutes and b_start < a_start + a.duration_minutes:
                conflicts.append((a, b))
        return conflicts

    def filter_tasks(self, day: date, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return the day's tasks matching the given pet and/or completion status."""
        tasks = self.get_daily_tasks(day)
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.is_completed_on(day) == completed]
        return tasks
