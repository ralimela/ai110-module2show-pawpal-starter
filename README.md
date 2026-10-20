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

- **`Task`** (dataclass): one care activity with a title, category, duration, priority (High/Medium/Low), frequency (Once/Daily/Weekly), due date, and optional start time. It tracks completion per date, so finishing Monday's daily walk doesn't mark Tuesday's done, and `occurs_on(day)` decides whether it happens on a given day.
- **`Pet`** (dataclass): a pet's name, species, and age plus its list of tasks. It adds, removes, and reschedules its own tasks; moving one occurrence of a recurring task skips that date and adds a one-time copy on the new date.
- **`Owner`** (dataclass): the user and their pets. `get_all_tasks()` gathers every pet's tasks into one list.
- **`Scheduler`**: the "brain." It reads from `Owner.get_all_tasks()` so it covers all pets, then builds the sorted daily list, a 7-day calendar, the day's total minutes, overlap warnings for fixed-time tasks, and filters by pet or completion status.

`main.py` is a CLI demo that builds a sample owner with two pets and prints today's schedule. `tests/test_pawpal.py` holds the pytest suite.

## 🖥️ Sample Output

Output from running `python main.py`, which creates an owner with two pets and six tasks, then prints today's schedule:

```
Today's Schedule for Jordan - Tuesday, October 20, 2026
==============================================================
      Time      Task                 Pet       Length  Priority
--------------------------------------------------------------
  [x] 07:30 AM  Morning walk         Rex       30 min  High
  [ ] 08:15 AM  Breakfast            Rex       10 min  High
  [ ] 02:30 PM  Flea medicine        Mia        5 min  High
  [ ] 02:00 PM  Vet checkup          Mia       60 min  Medium
  [ ] Anytime   Play time            Mia       20 min  Medium
  [ ] Anytime   Brush coat           Rex       15 min  Low
--------------------------------------------------------------
  Total time: 140 min

  Time conflicts:
    ! Flea medicine (Mia) overlaps Vet checkup (Mia)
```

Tasks are sorted High > Medium > Low; within a priority, fixed-time tasks come first in time order. `[x]` marks a task already completed today.

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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
