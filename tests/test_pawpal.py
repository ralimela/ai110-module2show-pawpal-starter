"""Quick tests for PawPal+ core behaviors."""

from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task

DAY = date(2026, 10, 20)


def make_scheduler(*tasks: Task) -> Scheduler:
    """Return a scheduler for one owner whose single pet has the given tasks."""
    owner = Owner("Jordan")
    pet = Pet("Rex", "Dog", 4)
    owner.add_pet(pet)
    for task in tasks:
        pet.add_task(task)
    return Scheduler(owner)


def test_mark_complete_changes_status():
    task = Task("Morning walk", "walk", 30, "High", DAY)

    assert not task.completed
    task.mark_complete()
    assert task.completed
    assert task.is_completed_on(DAY)


def test_add_task_increases_pet_task_count():
    pet = Pet("Rex", "Dog", 4)
    task = Task("Breakfast", "feeding", 10, "High", DAY)

    assert len(pet.get_tasks()) == 0
    pet.add_task(task)
    assert len(pet.get_tasks()) == 1


def test_sort_by_time_orders_by_clock_with_anytime_last():
    late = Task("Dinner", "feeding", 10, "High", DAY, start_time=time(18, 0))
    anytime = Task("Brush", "grooming", 10, "High", DAY)
    early = Task("Walk", "walk", 30, "Low", DAY, start_time=time(7, 30))

    assert Scheduler.sort_by_time([late, anytime, early]) == [early, late, anytime]


def test_filter_tasks_by_pet_and_status():
    walk = Task("Walk", "walk", 30, "High", DAY)
    meds = Task("Meds", "meds", 5, "High", DAY)
    scheduler = make_scheduler(walk, meds)
    mia = Pet("Mia", "Cat", 2)
    scheduler.owner.add_pet(mia)
    mia.add_task(Task("Play", "other", 20, "Low", DAY))
    scheduler.mark_task_complete(walk, DAY)

    assert [t.title for t in scheduler.filter_tasks(DAY, pet_name="Mia")] == ["Play"]
    assert scheduler.filter_tasks(DAY, completed=True) == [walk]
    assert [t.title for t in scheduler.filter_tasks(DAY, pet_name="Rex", completed=False)] == ["Meds"]


def test_completing_daily_task_creates_next_day_occurrence():
    walk = Task("Walk", "walk", 30, "High", DAY, "Daily")
    scheduler = make_scheduler(walk)

    next_walk = scheduler.mark_task_complete(walk, DAY)

    assert next_walk.due_date == DAY + timedelta(days=1)
    assert not next_walk.completed
    assert next_walk in scheduler.owner.pets[0].tasks
    assert scheduler.get_daily_tasks(DAY + timedelta(days=1)) == [next_walk]


def test_completing_weekly_task_creates_occurrence_seven_days_later():
    meds = Task("Flea meds", "meds", 5, "High", DAY, "Weekly")
    scheduler = make_scheduler(meds)

    assert scheduler.mark_task_complete(meds, DAY).due_date == DAY + timedelta(days=7)


def test_completing_once_task_creates_nothing():
    vet = Task("Vet", "appointment", 60, "High", DAY)
    scheduler = make_scheduler(vet)

    assert scheduler.mark_task_complete(vet, DAY) is None
    assert len(scheduler.owner.get_all_tasks()) == 1


def test_completing_later_occurrence_keeps_earlier_days_open():
    walk = Task("Walk", "walk", 30, "High", DAY, "Daily")
    scheduler = make_scheduler(walk)
    later = DAY + timedelta(days=2)

    scheduler.mark_task_complete(walk, later)

    assert scheduler.filter_tasks(later, completed=True)[0].title == "Walk"
    assert scheduler.filter_tasks(DAY, completed=False) == [walk]
    assert len(scheduler.get_daily_tasks(later)) == 1  # no duplicate walk on that day


def test_conflict_warning_for_same_start_time():
    a = Task("Walk", "walk", 30, "High", DAY, start_time=time(8, 0))
    b = Task("Breakfast", "feeding", 10, "High", DAY, start_time=time(8, 0))
    scheduler = make_scheduler(a, b)

    warnings = scheduler.get_conflict_warnings(DAY)

    assert len(warnings) == 1
    assert "same time" in warnings[0]


def test_no_conflict_when_tasks_touch_but_do_not_overlap():
    a = Task("Walk", "walk", 30, "High", DAY, start_time=time(8, 0))
    b = Task("Breakfast", "feeding", 10, "High", DAY, start_time=time(8, 30))

    assert make_scheduler(a, b).get_conflict_warnings(DAY) == []
