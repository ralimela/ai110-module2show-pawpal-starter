"""Quick tests for PawPal+ core behaviors."""

from datetime import date, time, timedelta

import pytest

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


# --- Edge cases ------------------------------------------------------------

def test_owner_with_no_pets_has_empty_schedule():
    scheduler = Scheduler(Owner("Jordan"))

    assert scheduler.get_daily_tasks(DAY) == []
    assert scheduler.total_duration(DAY) == 0
    assert scheduler.get_conflict_warnings(DAY) == []


def test_pet_with_no_tasks_has_empty_schedule():
    scheduler = make_scheduler()

    assert scheduler.get_daily_tasks(DAY) == []
    assert scheduler.filter_tasks(DAY, pet_name="Rex") == []


def test_daily_schedule_sorts_by_priority_then_time():
    low = Task("Brush", "grooming", 10, "Low", DAY, start_time=time(7, 0))
    high_late = Task("Meds", "meds", 5, "High", DAY, start_time=time(9, 0))
    high_early = Task("Walk", "walk", 30, "High", DAY, start_time=time(8, 0))
    high_anytime = Task("Play", "other", 20, "High", DAY)

    daily = make_scheduler(low, high_late, high_early, high_anytime).get_daily_tasks(DAY)

    assert daily == [high_early, high_late, high_anytime, low]


def test_sort_by_time_keeps_same_time_tasks_and_does_not_change_input():
    a = Task("Walk", "walk", 30, "High", DAY, start_time=time(8, 0))
    b = Task("Breakfast", "feeding", 10, "High", DAY, start_time=time(8, 0))
    tasks = [b, a]

    assert Scheduler.sort_by_time(tasks) == [b, a]  # ties keep their original order
    assert tasks == [b, a]


def test_task_does_not_occur_before_due_date():
    walk = Task("Walk", "walk", 30, "High", DAY, "Daily")

    assert not walk.occurs_on(DAY - timedelta(days=1))
    assert walk.occurs_on(DAY + timedelta(days=30))


def test_weekly_task_only_occurs_every_seven_days():
    meds = Task("Flea meds", "meds", 5, "High", DAY, "Weekly")
    calendar = make_scheduler(meds).get_weekly_calendar(DAY)

    assert len(calendar) == 7
    assert [day for day, tasks in calendar.items() if tasks] == [DAY]
    assert meds.occurs_on(DAY + timedelta(days=7))


def test_completing_same_task_twice_creates_only_one_next_occurrence():
    walk = Task("Walk", "walk", 30, "High", DAY, "Daily")
    scheduler = make_scheduler(walk)

    scheduler.mark_task_complete(walk, DAY)
    assert scheduler.mark_task_complete(walk, DAY) is None
    assert len(scheduler.owner.get_all_tasks()) == 2


def test_recurring_chain_shows_one_task_per_day():
    walk = Task("Walk", "walk", 30, "High", DAY, "Daily")
    scheduler = make_scheduler(walk)
    tomorrow = DAY + timedelta(days=1)

    next_walk = scheduler.mark_task_complete(walk, DAY)
    scheduler.mark_task_complete(next_walk, tomorrow)

    for day in (DAY, tomorrow, DAY + timedelta(days=2)):
        assert len(scheduler.get_daily_tasks(day)) == 1
    assert scheduler.filter_tasks(tomorrow, completed=True) == [next_walk]


def test_completing_task_on_wrong_day_raises():
    vet = Task("Vet", "appointment", 60, "High", DAY)
    scheduler = make_scheduler(vet)

    with pytest.raises(ValueError):
        scheduler.mark_task_complete(vet, DAY + timedelta(days=1))


def test_completing_task_not_owned_by_any_pet_raises():
    scheduler = make_scheduler()
    stray = Task("Walk", "walk", 30, "High", DAY)

    with pytest.raises(ValueError):
        scheduler.mark_task_complete(stray, DAY)


def test_conflicts_flag_same_time_across_different_pets():
    scheduler = make_scheduler(Task("Walk", "walk", 30, "High", DAY, start_time=time(8, 0)))
    mia = Pet("Mia", "Cat", 2)
    scheduler.owner.add_pet(mia)
    mia.add_task(Task("Breakfast", "feeding", 5, "High", DAY, start_time=time(8, 0)))

    warnings = scheduler.get_conflict_warnings(DAY)

    assert len(warnings) == 1
    assert "Rex" in warnings[0] and "Mia" in warnings[0]


def test_conflicts_ignore_anytime_tasks_and_other_days():
    walk = Task("Walk", "walk", 30, "High", DAY, start_time=time(8, 0))
    anytime = Task("Brush", "grooming", 60, "Low", DAY)
    tomorrow_vet = Task("Vet", "appointment", 60, "High", DAY + timedelta(days=1), start_time=time(8, 0))

    assert make_scheduler(walk, anytime, tomorrow_vet).detect_conflicts(DAY) == []


def test_reschedule_one_occurrence_of_daily_task():
    walk = Task("Walk", "walk", 30, "High", DAY, "Daily")
    scheduler = make_scheduler(walk)
    pet = scheduler.owner.pets[0]
    tomorrow = DAY + timedelta(days=1)

    pet.reschedule_task(walk, DAY, tomorrow)

    assert scheduler.get_daily_tasks(DAY) == []
    assert len(scheduler.get_daily_tasks(tomorrow)) == 2  # the moved walk plus tomorrow's regular walk


def test_invalid_task_values_raise():
    with pytest.raises(ValueError):
        Task("Walk", "walk", 30, "high", DAY)  # priority is case-sensitive
    with pytest.raises(ValueError):
        Task("Walk", "walk", 30, "High", DAY, "Monthly")
    with pytest.raises(ValueError):
        Task("Walk", "walk", 0, "High", DAY)
