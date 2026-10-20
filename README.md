# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

All backend logic lives in `pawpal_system.py`, built from four classes:

- **`Task`** (dataclass): one care activity with a title, category, duration, priority (High/Medium/Low), frequency (Once/Daily/Weekly), due date, and optional start time. `occurs_on(day)` decides whether it happens on a given day. Marking a Daily or Weekly task complete returns a fresh copy for the next occurrence, so finishing Monday's walk doesn't mark Tuesday's done.
- **`Pet`** (dataclass): a pet's name, species, and age plus its list of tasks. It adds, removes, completes, and reschedules its own tasks, and it stores the next occurrence when a recurring task is completed.
- **`Owner`** (dataclass): the user and their pets. `get_all_tasks()` gathers every pet's tasks into one list.
- **`Scheduler`**: the "brain." It reads from `Owner.get_all_tasks()` so it covers all pets, then builds the sorted daily list, a 7-day calendar, and the day's total minutes. It also sorts by time, filters by pet or completion status, completes tasks, and warns about time conflicts (see Smarter Scheduling below).

`app.py` is the Streamlit UI and keeps the `Owner` in `st.session_state` so data survives reruns. `main.py` is a CLI demo that builds a sample owner with two pets and exercises every scheduler feature. `tests/test_pawpal.py` holds the pytest suite.

## 🖥️ Sample Output

Output from running `python main.py`, which creates an owner with two pets and eight tasks (added out of time order), then prints today's schedule and exercises sorting, filtering, recurring tasks, and conflict detection:

```
PawPal+ for Jordan - Tuesday, October 20, 2026
==============================================================

Today's Schedule (by priority)
--------------------------------------------------------------
      Time      Task                 Pet       Length  Priority
  [ ] 07:30 AM  Morning walk         Rex       30 min  High
  [ ] 08:00 AM  Breakfast            Rex       10 min  High
  [ ] 08:00 AM  Breakfast            Mia        5 min  High
  [ ] 02:30 PM  Flea medicine        Mia        5 min  High
  [ ] 02:00 PM  Vet checkup          Mia       60 min  Medium
  [ ] 06:00 PM  Evening walk         Rex       30 min  Medium
  [ ] Anytime   Play time            Mia       20 min  Medium
  [ ] Anytime   Brush coat           Rex       15 min  Low
  Total time: 175 min

Sorted by time - Scheduler.sort_by_time()
--------------------------------------------------------------
      Time      Task                 Pet       Length  Priority
  [ ] 07:30 AM  Morning walk         Rex       30 min  High
  [ ] 08:00 AM  Breakfast            Rex       10 min  High
  [ ] 08:00 AM  Breakfast            Mia        5 min  High
  [ ] 02:00 PM  Vet checkup          Mia       60 min  Medium
  [ ] 02:30 PM  Flea medicine        Mia        5 min  High
  [ ] 06:00 PM  Evening walk         Rex       30 min  Medium
  [ ] Anytime   Play time            Mia       20 min  Medium
  [ ] Anytime   Brush coat           Rex       15 min  Low

Only Mia's tasks - filter_tasks(pet_name='Mia')
--------------------------------------------------------------
      Time      Task                 Pet       Length  Priority
  [ ] 08:00 AM  Breakfast            Mia        5 min  High
  [ ] 02:30 PM  Flea medicine        Mia        5 min  High
  [ ] 02:00 PM  Vet checkup          Mia       60 min  Medium
  [ ] Anytime   Play time            Mia       20 min  Medium

Recurring tasks - Scheduler.mark_task_complete()
--------------------------------------------------------------
  Completed 'Morning walk' (Daily) for Oct 20.
  Next occurrence created: 'Morning walk' due Wednesday, Oct 21.

Done today - filter_tasks(completed=True)
--------------------------------------------------------------
      Time      Task                 Pet       Length  Priority
  [x] 07:30 AM  Morning walk         Rex       30 min  High

Still to do - filter_tasks(completed=False)
--------------------------------------------------------------
      Time      Task                 Pet       Length  Priority
  [ ] 08:00 AM  Breakfast            Rex       10 min  High
  [ ] 08:00 AM  Breakfast            Mia        5 min  High
  [ ] 02:30 PM  Flea medicine        Mia        5 min  High
  [ ] 02:00 PM  Vet checkup          Mia       60 min  Medium
  [ ] 06:00 PM  Evening walk         Rex       30 min  Medium
  [ ] Anytime   Play time            Mia       20 min  Medium
  [ ] Anytime   Brush coat           Rex       15 min  Low

Conflicts - Scheduler.get_conflict_warnings()
--------------------------------------------------------------
  WARNING: Breakfast (Rex) and Breakfast (Mia) are both at the same time, 08:00 AM
  WARNING: Vet checkup (Mia, 02:00 PM, 60 min) overlaps Flea medicine (Mia, 02:30 PM)
```

The main schedule is sorted High > Medium > Low; within a priority, fixed-time tasks come first in time order. `[x]` marks a task completed today.

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | How it works |
|---------|-----------|--------------|
| Sorting by time | `Scheduler.sort_by_time(tasks)` | `sorted()` with a lambda key `(t.start_time is None, t.start_time or time.min)`: fixed-time tasks in clock order, "Anytime" tasks last. |
| Sorting by priority | `Scheduler.get_daily_tasks(day)` | Sorts by time first, then by priority (High > Medium > Low). Python's sort is stable, so tasks keep time order within each priority. |
| Filtering | `Scheduler.filter_tasks(day, pet_name=None, completed=None)` | Narrows a day's tasks to one pet, to done/not-done tasks, or both. |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()`, `Pet.complete_task()`, `Scheduler.mark_task_complete()` | Completing a Daily/Weekly task creates a new task for the next occurrence, due `due_date + timedelta(days=1)` (Daily) or `timedelta(days=7)` (Weekly). Once tasks create nothing. `Task.occurs_on(day)` decides which days a task appears on. |
| Conflict detection | `Scheduler.detect_conflicts(day)`, `Scheduler.get_conflict_warnings(day)` | Checks every pair of fixed-time tasks on the day, for the same pet or different pets, and flags exact same-time starts and overlapping durations. Returns readable warning strings (an empty list if there are none) instead of raising an error. |
| Weekly view | `Scheduler.get_weekly_calendar(start_day)` | Seven days, each with its sorted task list. |
| Rescheduling | `Pet.reschedule_task(task, from_date, new_date)` | Moves a one-time task, or moves just one occurrence of a recurring task to a new day. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
