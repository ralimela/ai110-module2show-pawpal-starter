"""Demo script: build a sample owner with two pets and exercise the scheduler in the terminal."""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def format_task(task: Task, day: date) -> str:
    """Return one aligned schedule line for a task."""
    when = task.start_time.strftime("%I:%M %p") if task.start_time else "Anytime"
    status = "[x]" if task.is_completed_on(day) else "[ ]"
    return (f"  {status} {when:<9} {task.title:<20} {task.pet_name:<8} "
            f"{task.duration_minutes:>3} min  {task.priority}")


def print_tasks(heading: str, tasks: list[Task], day: date) -> None:
    """Print a heading, a column header, and one line per task."""
    print(f"\n{heading}")
    print("-" * 62)
    print(f"      {'Time':<9} {'Task':<20} {'Pet':<8} {'Length':>7}  Priority")
    for task in tasks:
        print(format_task(task, day))
    if not tasks:
        print("  (no tasks)")


def main() -> None:
    """Build sample data and print the schedule, sorting, filtering, recurrence, and conflicts."""
    today = date.today()

    owner = Owner("Jordan")
    rex = Pet("Rex", "Dog", 4)
    mia = Pet("Mia", "Cat", 2)
    owner.add_pet(rex)
    owner.add_pet(mia)

    # Added out of time order on purpose so sort_by_time() has work to do.
    mia.add_task(Task("Vet checkup", "appointment", 60, "Medium", today, start_time=time(14, 0)))
    rex.add_task(Task("Evening walk", "walk", 30, "Medium", today, "Daily", start_time=time(18, 0)))
    rex.add_task(Task("Brush coat", "grooming", 15, "Low", today))
    mia.add_task(Task("Flea medicine", "meds", 5, "High", today, "Weekly", start_time=time(14, 30)))
    rex.add_task(Task("Breakfast", "feeding", 10, "High", today, "Daily", start_time=time(8, 0)))
    mia.add_task(Task("Play time", "other", 20, "Medium", today, "Daily"))
    rex.add_task(Task("Morning walk", "walk", 30, "High", today, "Daily", start_time=time(7, 30)))
    mia.add_task(Task("Breakfast", "feeding", 5, "High", today, "Daily", start_time=time(8, 0)))

    scheduler = Scheduler(owner)

    print(f"PawPal+ for {owner.name} - {today:%A, %B %d, %Y}")
    print("=" * 62)

    print_tasks("Today's Schedule (by priority)", scheduler.get_daily_tasks(today), today)
    print(f"  Total time: {scheduler.total_duration(today)} min")

    print_tasks("Sorted by time - Scheduler.sort_by_time()",
                scheduler.sort_by_time(scheduler.get_daily_tasks(today)), today)

    print_tasks("Only Mia's tasks - filter_tasks(pet_name='Mia')",
                scheduler.filter_tasks(today, pet_name="Mia"), today)

    # Recurring task: completing today's Daily walk creates tomorrow's walk.
    walk = next(t for t in rex.tasks if t.title == "Morning walk")
    next_walk = scheduler.mark_task_complete(walk, today)
    print("\nRecurring tasks - Scheduler.mark_task_complete()")
    print("-" * 62)
    print(f"  Completed '{walk.title}' ({walk.frequency}) for {today:%b %d}.")
    print(f"  Next occurrence created: '{next_walk.title}' due {next_walk.due_date:%A, %b %d}.")

    print_tasks("Done today - filter_tasks(completed=True)",
                scheduler.filter_tasks(today, completed=True), today)
    print_tasks("Still to do - filter_tasks(completed=False)",
                scheduler.filter_tasks(today, completed=False), today)

    print("\nConflicts - Scheduler.get_conflict_warnings()")
    print("-" * 62)
    warnings = scheduler.get_conflict_warnings(today)
    for warning in warnings:
        print(f"  WARNING: {warning}")
    if not warnings:
        print("  No conflicts.")


if __name__ == "__main__":
    main()
