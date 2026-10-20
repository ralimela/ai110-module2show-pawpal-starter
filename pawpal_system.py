"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler classes."""

from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from itertools import combinations

PRIORITIES = ("High", "Medium", "Low")
FREQUENCIES = ("Once", "Daily", "Weekly")
PRIORITY_RANKS = {"High": 3, "Medium": 2, "Low": 1}
FREQUENCY_DAYS = {"Daily": 1, "Weekly": 7}  # days between occurrences of a recurring task


@dataclass
class Task:
    """A single pet care activity (walk, feeding, meds, appointment, etc.)."""

    title: str
    category: str                  # walk / feeding / meds / grooming / appointment / other
    duration_minutes: int
    priority: str                  # one of PRIORITIES
    due_date: date                 # Once: the day it happens; Daily/Weekly: the next open occurrence
    frequency: str = "Once"        # one of FREQUENCIES
    start_time: time | None = None # only for fixed-time tasks like appointments
    pet_name: str = ""             # set by Pet.add_task so lists can show whose task it is
    completed: bool = False
    skipped_dates: list[date] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Reject priority/frequency values that aren't in PRIORITIES/FREQUENCIES."""
        if self.priority not in PRIORITIES:
            raise ValueError(f"priority must be one of {PRIORITIES}, got {self.priority!r}")
        if self.frequency not in FREQUENCIES:
            raise ValueError(f"frequency must be one of {FREQUENCIES}, got {self.frequency!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be greater than 0")

    def mark_complete(self) -> "Task | None":
        """Mark this occurrence done and return the next occurrence (None for Once tasks)."""
        self.completed = True
        return self.next_occurrence()

    def next_occurrence(self) -> "Task | None":
        """Return an open copy due one interval later (+1 day Daily, +7 days Weekly), or None for Once."""
        if self.frequency == "Once":
            return None
        next_due = self.due_date + timedelta(days=FREQUENCY_DAYS[self.frequency])
        return replace(self, due_date=next_due, completed=False, skipped_dates=list(self.skipped_dates))

    def is_completed_on(self, day: date) -> bool:
        """Return True if this task was marked done for the given day."""
        return self.completed and day == self.due_date

    def priority_rank(self) -> int:
        """Return a sortable number for priority: High=3, Medium=2, Low=1."""
        return PRIORITY_RANKS[self.priority]

    def occurs_on(self, day: date) -> bool:
        """Return True if this task happens on the given day (based on frequency and skipped_dates).

        A completed recurring task only covers its own due_date; the next occurrence
        created by mark_complete() covers the days after it.
        """
        if day in self.skipped_dates or day < self.due_date:
            return False
        if self.frequency == "Once" or self.completed:
            return day == self.due_date
        return (day - self.due_date).days % FREQUENCY_DAYS[self.frequency] == 0


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

    def complete_task(self, task: Task, day: date) -> Task | None:
        """Mark task done on day and return the next occurrence it created, if any.

        Completing a recurring task's current occurrence (day == due_date) adds a new
        task for the next occurrence. Completing a later occurrence early splits that
        day off as a completed one-time copy, so the series keeps its earlier days.
        """
        self._check_occurrence(task, day)
        if task.is_completed_on(day):
            return None
        if day != task.due_date:
            self._split_off(task, day, day).completed = True
            return None
        next_task = task.mark_complete()
        if next_task is not None:
            self.add_task(next_task)
        return next_task

    def reschedule_task(self, task: Task, from_date: date, new_date: date) -> None:
        """Move one occurrence of task from from_date to new_date.

        Once tasks: change due_date.
        Daily/Weekly tasks: add from_date to skipped_dates and add a new Once copy on new_date.
        """
        self._check_occurrence(task, from_date)
        if task.completed:
            raise ValueError(f"{task.title!r} is already completed")

        if task.frequency == "Once":
            task.due_date = new_date
        else:
            self._split_off(task, from_date, new_date)

    def _check_occurrence(self, task: Task, day: date) -> None:
        """Raise ValueError unless task belongs to this pet and happens on day."""
        if not any(t is task for t in self.tasks):
            raise ValueError(f"{task.title!r} is not one of {self.name}'s tasks")
        if not task.occurs_on(day):
            raise ValueError(f"{task.title!r} does not occur on {day}")

    def _split_off(self, task: Task, day: date, new_date: date) -> Task:
        """Skip day in a recurring task and add a one-time copy of that occurrence on new_date."""
        task.skipped_dates.append(day)
        copy = replace(task, due_date=new_date, frequency="Once", completed=False, skipped_dates=[])
        self.add_task(copy)
        return copy


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

    @staticmethod
    def sort_by_time(tasks: list[Task]) -> list[Task]:
        """Return tasks in clock order; tasks with no start time ("Anytime") go last."""
        return sorted(tasks, key=lambda t: (t.start_time is None, t.start_time or time.min))

    def get_daily_tasks(self, day: date) -> list[Task]:
        """Return tasks that occur on day, sorted High -> Medium -> Low.

        Within the same priority, fixed-time tasks come first in time order.
        """
        tasks = [t for t in self.owner.get_all_tasks() if t.occurs_on(day)]
        # sorted() is stable, so tasks keep their time order within each priority
        return sorted(self.sort_by_time(tasks), key=lambda t: -t.priority_rank())

    def get_weekly_calendar(self, start_day: date) -> dict[date, list[Task]]:
        """Return 7 days starting at start_day, each mapped to its sorted tasks."""
        days = (start_day + timedelta(days=i) for i in range(7))
        return {day: self.get_daily_tasks(day) for day in days}

    def total_duration(self, day: date) -> int:
        """Return the total minutes of all tasks on day."""
        return sum(t.duration_minutes for t in self.get_daily_tasks(day))

    def filter_tasks(self, day: date, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return the day's tasks matching the given pet and/or completion status."""
        tasks = self.get_daily_tasks(day)
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.is_completed_on(day) == completed]
        return tasks

    def mark_task_complete(self, task: Task, day: date) -> Task | None:
        """Complete task on day through its pet; return the next occurrence created, if any."""
        for pet in self.owner.pets:
            if any(t is task for t in pet.tasks):
                return pet.complete_task(task, day)
        raise ValueError(f"{task.title!r} does not belong to any of {self.owner.name}'s pets")

    def detect_conflicts(self, day: date) -> list[tuple[Task, Task]]:
        """Return pairs of fixed-time tasks on day whose time ranges overlap (any pets)."""
        def minutes(t: time) -> int:
            """Convert a time of day to minutes since midnight."""
            return t.hour * 60 + t.minute

        timed = self.sort_by_time([t for t in self.get_daily_tasks(day) if t.start_time is not None])
        conflicts = []
        for a, b in combinations(timed, 2):
            a_start, b_start = minutes(a.start_time), minutes(b.start_time)
            if a_start < b_start + b.duration_minutes and b_start < a_start + a.duration_minutes:
                conflicts.append((a, b))
        return conflicts

    def get_conflict_warnings(self, day: date) -> list[str]:
        """Return a readable warning for each conflict on day (empty list if none); never raises."""
        warnings = []
        for a, b in self.detect_conflicts(day):
            if a.start_time == b.start_time:
                warnings.append(f"WARNING: {a.title} ({a.pet_name}) and {b.title} ({b.pet_name}) "
                                f"are both at the same time, {a.start_time:%I:%M %p}")
            else:
                warnings.append(f"WARNING: {a.title} ({a.pet_name}, {a.start_time:%I:%M %p}, "
                                f"{a.duration_minutes} min) overlaps {b.title} ({b.pet_name}, {b.start_time:%I:%M %p})")
        return warnings
