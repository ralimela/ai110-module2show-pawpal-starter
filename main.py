"""Demo script: build a sample owner with two pets and print today's schedule."""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def format_task(task: Task, day: date) -> str:
    """Return one aligned schedule line for a task."""
    when = task.start_time.strftime("%I:%M %p") if task.start_time else "Anytime"
    status = "[x]" if task.is_completed_on(day) else "[ ]"
    return (f"  {status} {when:<9} {task.title:<20} {task.pet_name:<8} "
            f"{task.duration_minutes:>3} min  {task.priority}")


def print_schedule(scheduler: Scheduler, day: date) -> None:
    """Print the day's tasks, total time, and any time conflicts."""
    print(f"Today's Schedule for {scheduler.owner.name} - {day:%A, %B %d, %Y}")
    print("=" * 62)
    print(f"      {'Time':<9} {'Task':<20} {'Pet':<8} {'Length':>7}  Priority")
    print("-" * 62)
    for task in scheduler.get_daily_tasks(day):
        print(format_task(task, day))
    print("-" * 62)
    print(f"  Total time: {scheduler.total_duration(day)} min")

    conflicts = scheduler.detect_conflicts(day)
    if conflicts:
        print("\n  Time conflicts:")
        for a, b in conflicts:
            print(f"    ! {a.title} ({a.pet_name}) overlaps {b.title} ({b.pet_name})")


def main() -> None:
    today = date.today()

    owner = Owner("Jordan")
    rex = Pet("Rex", "Dog", 4)
    mia = Pet("Mia", "Cat", 2)
    owner.add_pet(rex)
    owner.add_pet(mia)

    rex.add_task(Task("Morning walk", "walk", 30, "High", today, "Daily", start_time=time(7, 30)))
    rex.add_task(Task("Breakfast", "feeding", 10, "High", today, "Daily", start_time=time(8, 15)))
    rex.add_task(Task("Brush coat", "grooming", 15, "Low", today))
    mia.add_task(Task("Vet checkup", "appointment", 60, "Medium", today, start_time=time(14, 0)))
    mia.add_task(Task("Flea medicine", "meds", 5, "High", today, "Weekly", start_time=time(14, 30)))
    mia.add_task(Task("Play time", "other", 20, "Medium", today, "Daily"))

    rex.tasks[0].mark_complete(today)  # the morning walk is already done

    print_schedule(Scheduler(owner), today)


if __name__ == "__main__":
    main()
