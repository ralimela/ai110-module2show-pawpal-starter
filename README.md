# 🐾 PawPal+

PawPal+ is a pet care planner for busy owners. It keeps track of every pet's feedings, walks, medications, grooming, and appointments, builds a prioritized daily schedule, handles daily and weekly repeats, and warns you when two tasks collide. It is built as a Python logic layer (`pawpal_system.py`) with a Streamlit UI (`app.py`), a CLI demo (`main.py`), and a pytest suite.

## ✨ Features

- **Multiple pets per owner:** each pet keeps its own task list, and the scheduler combines them all into one plan.
- **Priority-first daily schedule:** tasks are ordered High > Medium > Low, and within each priority fixed-time tasks come first in clock order, then "Anytime" tasks.
- **Sorting by time:** switch to a clock-order view (07:30, 08:00, ... then "Anytime") with `Scheduler.sort_by_time()`.
- **Filtering:** show one pet's tasks, only to-do tasks, only done tasks, or any combination.
- **Daily and weekly recurrence:** marking a Daily task done automatically creates tomorrow's task (`timedelta(days=1)`); Weekly creates next week's (`timedelta(days=7)`). One-time tasks just get checked off.
- **Conflict warnings:** flags fixed-time tasks that start at the exact same time or overlap (for example, a 60-minute vet visit at 2:00 PM and medication at 2:30 PM), for the same pet or different pets. Warnings are friendly messages, never crashes.
- **Daily totals and progress:** total minutes of care for the day, and how many tasks are done.
- **7-day overview:** a week at a glance with task counts, minutes, and conflicts per day.
- **Rescheduling:** move a one-time task, or just one occurrence of a repeating task, to another day.
- **Input validation:** invalid priorities, frequencies, or durations are rejected with a clear error.

## 🚀 Getting Started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run it

```bash
streamlit run app.py     # the web app
python main.py           # the CLI demo
python -m pytest         # the test suite
```

### Project structure

| File | Purpose |
|------|---------|
| `pawpal_system.py` | Logic layer: `Task`, `Pet`, `Owner`, and `Scheduler` classes |
| `app.py` | Streamlit UI that stores the `Owner` in `st.session_state` and calls the `Scheduler` |
| `main.py` | CLI demo that exercises every scheduler feature |
| `tests/test_pawpal.py` | 24 pytest tests |
| `diagrams/uml_final.mmd` | Final Mermaid UML class diagram |
| `reflection.md` | Design decisions, tradeoffs, and AI collaboration reflection |

## 🛠️ Implementation Summary

All backend logic lives in `pawpal_system.py`, built from four classes:

- **`Task`** (dataclass): one care activity with a title, category, duration, priority (High/Medium/Low), frequency (Once/Daily/Weekly), due date, and optional start time. `occurs_on(day)` decides whether it happens on a given day. Marking a Daily or Weekly task complete returns a fresh copy for the next occurrence, so finishing Monday's walk doesn't mark Tuesday's done.
- **`Pet`** (dataclass): a pet's name, species, and age plus its list of tasks. It adds, removes, completes, and reschedules its own tasks, and it stores the next occurrence when a recurring task is completed.
- **`Owner`** (dataclass): the user and their pets. `get_all_tasks()` gathers every pet's tasks into one list.
- **`Scheduler`**: the "brain." It reads from `Owner.get_all_tasks()` so it covers all pets, then builds the sorted daily list, a 7-day calendar, and the day's total minutes. It also sorts by time, filters by pet or completion status, completes tasks, and warns about time conflicts (see Smarter Scheduling below).

`app.py` keeps the `Owner` in `st.session_state`, so pets and tasks survive Streamlit's reruns, and every table, filter, and warning in the UI comes from a `Scheduler` method.

### 📐 UML

The final class diagram is in [`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) (paste it into the [Mermaid Live Editor](https://mermaid.live) to view it). `Owner` has many `Pet`s, each `Pet` has many `Task`s, the `Scheduler` reads every task through the `Owner`, and completing a recurring `Task` creates its next occurrence.

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

## 🧪 Testing PawPal+

Run the full test suite from the project folder (with the virtual environment active):

```bash
python -m pytest
```

The 24 tests in `tests/test_pawpal.py` cover:

- **Sorting:** `sort_by_time()` returns tasks in clock order with "Anytime" tasks last, keeps same-time tasks in their original order, and doesn't modify the input list. The daily list is High > Medium > Low, with time order inside each priority.
- **Filtering:** `filter_tasks()` by pet name, by done/not-done status, and by both together.
- **Recurring tasks:** completing a Daily task creates a new task for the next day, Weekly creates one 7 days later, and Once creates none. Completing the same task twice doesn't create duplicates, a chain of daily completions shows exactly one walk per day, and a task never appears before its due date.
- **Conflict detection:** flags tasks at the exact same time (including tasks for different pets), and doesn't flag tasks that only touch end to end, "Anytime" tasks, or tasks on other days.
- **Edge cases and validation:** an owner with no pets or a pet with no tasks gives an empty schedule. Completing a task on a day it doesn't occur, or one that belongs to no pet, raises `ValueError`, and so do invalid priority, frequency, or duration values. Rescheduling one occurrence of a daily task moves only that day.

Successful test run:

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.7.0
rootdir: E:\Codepath\ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 24 items

tests\test_pawpal.py ........................                            [100%]

============================= 24 passed in 0.06s ==============================
```

**Confidence Level: ★★★★☆ (4.5/5)**

All 24 tests pass, covering every scheduling feature plus its main edge cases (empty data, same-time tasks, duplicate completions, invalid input). It isn't 5 stars because the Streamlit UI is only checked by hand, and some situations aren't tested yet: tasks that run past midnight, very long task lists, and overdue recurring tasks that were never completed.

## 📸 Demo Walkthrough

### Main UI features

The Streamlit app (`streamlit run app.py`) is one page with three numbered sections plus a weekly overview:

1. **Owner name:** at the top; edit it any time.
2. **1. Pets:** a form to add a pet (name, species, age). Blank or duplicate names show an error. A table lists all pets.
3. **2. Tasks:** a form to schedule a task for a chosen pet: title, category, duration, priority, how often it repeats (Once/Daily/Weekly), the date, and an optional fixed start time for appointments or medications. Invalid values show an error instead of crashing.
4. **3. Schedule:** pick any date to see that day's plan:
   - **Conflict banner:** a yellow `st.warning` at the top lists every pair of clashing tasks with their times and suggests moving one, or a green "No time conflicts" message.
   - **Progress metrics:** number of tasks, how many are done, and total minutes.
   - **Sort and filter controls:** sort by Priority or Time of day, show All pets or one pet, and show All, To do, or Done tasks.
   - **Schedule table:** done status, time, task, pet, minutes, color-coded priority (🔴 High, 🟡 Medium, 🟢 Low), and repeat frequency.
   - **Mark done:** pick a task and click ✅ Mark done. For a Daily or Weekly task, a success message confirms the next occurrence was created.
5. **📅 7-day overview:** an expandable table with each day's task count, total minutes, conflict count, and what's planned.

### Example workflow

1. Enter your name as the owner, e.g. "Jordan".
2. Add two pets: **Rex** (Dog, 4) and **Mia** (Cat, 2).
3. Add a task for Rex: "Morning walk", walk, 30 min, High, repeats Daily, fixed time 8:00 AM.
4. Add a task for Mia: "Breakfast", feeding, 5 min, High, repeats Daily, fixed time 8:00 AM.
5. Add a task for Rex: "Brush coat", grooming, 15 min, Low, Once, no fixed time.
6. Look at **3. Schedule** for today: the yellow banner warns that *Morning walk (Rex) and Breakfast (Mia) are both at the same time, 08:00 AM*, and the metrics show 3 tasks, 0 / 3 done, 60 min.
7. Set the Pet filter to **Mia** to see only her breakfast, then switch back to All pets and sort by **Time of day**.
8. Mark **Morning walk** done. The app confirms *"Marked 'Morning walk' for Rex done. Next daily occurrence added for [tomorrow's date]."*, and the Done metric changes to 1 / 3.
9. Open the **📅 7-day overview** to see the walk and breakfast on every day of the week.

### Key Scheduler behaviors shown

- **Priority sorting** (`get_daily_tasks`): High tasks first; within a priority, fixed times in order, then "Anytime".
- **Time sorting** (`sort_by_time`): pure clock order, "Anytime" last.
- **Filtering** (`filter_tasks`): by pet and by done/to-do.
- **Daily recurrence** (`mark_task_complete`): completing today's walk creates tomorrow's.
- **Conflict warnings** (`get_conflict_warnings`): same-time and overlapping tasks across pets.

### 🖥️ Sample Output (CLI)

Running `python main.py` creates an owner with two pets and eight tasks (added out of time order on purpose), then prints today's schedule and exercises sorting, filtering, recurring tasks, and conflict detection:

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

The main schedule is sorted High > Medium > Low; within a priority, fixed-time tasks come first in time order. `[x]` marks a task completed today. Notice that Flea medicine (2:30 PM, High) comes before Vet checkup (2:00 PM, Medium) in the priority view but after it in the time view.
