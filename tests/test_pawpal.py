"""Quick tests for PawPal+ core behaviors."""

from datetime import date

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    day = date(2026, 10, 20)
    task = Task("Morning walk", "walk", 30, "High", day)

    assert not task.is_completed_on(day)
    task.mark_complete(day)
    assert task.is_completed_on(day)


def test_add_task_increases_pet_task_count():
    pet = Pet("Rex", "Dog", 4)
    task = Task("Breakfast", "feeding", 10, "High", date(2026, 10, 20))

    assert len(pet.get_tasks()) == 0
    pet.add_task(task)
    assert len(pet.get_tasks()) == 1
