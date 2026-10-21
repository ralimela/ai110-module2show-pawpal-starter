# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**Core user actions:**

1) Add a new pet and enter its basic info like the pet's name, species, and age, along with the owner's name.
2) Schedule day to day tasks - create tasks such as walks, feedings, medications or vet appointments, each with a duration, a priority (High/Medium/Low), and a recurrence (Once/Daily/Weekly). Fixed-time tasks like appointments can also have a start time.
3) View today's tasks and the week - the app shows today's tasks sorted High > Medium > Low with each task's duration and the day's total, plus a weekly calendar view. The owner decides what to do and can move a task to another day if they can't finish it.

**Classes and responsibilities:**

My UML has four classes. Owner has many Pets, each Pet has many Tasks, and the Scheduler uses the Owner to reach every task.

- **Task** (dataclass): one care activity. It holds the title, category, duration, priority, recurrence, due date, and optional start time. It knows how to rank its priority (High=3, Medium=2, Low=1), whether it occurs on a given day, and how to be marked complete.
- **Pet** (dataclass): one animal (name, species, age) and its list of tasks. It adds, removes, and reschedules its own tasks.
- **Owner** (dataclass): the app user. It holds the list of pets and can collect every pet's tasks into one list.
- **Scheduler** (regular class): the logic layer. It builds the sorted daily list, the 7-day weekly calendar, and the day's total duration, detects time conflicts between fixed-time tasks, and filters tasks by pet or completion status.

I left out an owner "available time" limit on purpose. The app shows the sorted list and lets the owner decide what fits their day, which keeps the design simpler.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

After writing the skeleton, I asked my AI assistant to review pawpal_system.py for missing relationships and logic bottlenecks. I made these changes:

1. Renamed Task.date to due_date. A field named date has the same name as Python's datetime.date type, which is confusing and can cause bugs.
2. Replaced completed (a True/False flag) with completed_dates and mark_complete(day). With one flag, finishing Monday's daily walk would have marked the walk done for every day. Tracking completion per date fixes that.
3. Moved rescheduling from Task.reschedule(new_date) to Pet.reschedule_task(task, from_date, new_date). Moving one occurrence of a recurring task creates a new "Once" copy, and a Task has no way to add that copy to its pet's list. The old method also didn't know which occurrence to skip, so I added from_date.
4. Changed remove_task(title) to remove_task(task). Titles aren't unique: after a reschedule, a pet has two tasks with the same title.
5. Added pet_name to Task. Owner.get_all_tasks() returns one combined list, so the daily list couldn't show which pet a task belongs to. Pet.add_task now sets it.
6. Added validation for priority and frequency (the PRIORITIES and FREQUENCIES lists, checked in __post_init__). A typo like "high" instead of "High" would otherwise sort wrong without any error.

7. Later, in Phase 4, I replaced completed_dates with a simple completed flag plus "next occurrence" tasks. Now, when a Daily or Weekly task is marked complete, Task.mark_complete() returns a new copy due one interval later (using timedelta), and Pet.complete_task() adds it to the pet. Each Task object is one occurrence, which makes "done" and "not done" easy to filter and matches how an owner thinks about it: today's walk is finished, and tomorrow's is a new to-do.

The review also checked performance. The weekly calendar runs the daily lookup 7 times, and conflict detection compares tasks in pairs. Both are fine at the size of a household's pet tasks, so I kept them simple.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers four constraints:

1. **Priority (High/Medium/Low):** the main sort key, so the most important care, like medication, is always at the top of the day.
2. **Fixed start time:** appointments and medications can have a start time. Within each priority, timed tasks come first in clock order, and they're the only tasks checked for conflicts.
3. **Recurrence and date:** a task appears only on the days it actually happens (Once, every day, or every 7 days from its due date), never before its due date and never on a skipped day.
4. **Duration:** used to show the day's total minutes and to detect overlaps (a 60-minute 2:00 PM visit blocks until 3:00 PM).

I decided priority mattered most because missing a High task, like medication or a vet appointment, has real consequences for the pet, while a late brushing session doesn't. Fixed times came second because they're the constraints the owner can't move. I chose not to model the owner's "available time" as a hard limit. Instead the app shows the total minutes and lets the owner decide what fits, because an app guessing at someone's free time would often be wrong.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Tradeoff: conflict detection only checks tasks with a fixed start time.** The scheduler compares every pair of timed tasks on a day and flags exact same-time starts and overlapping durations (for example, a 2:00 PM vet visit that lasts 60 minutes overlaps 2:30 PM flea medicine). "Anytime" tasks like brushing or play time are never flagged, and the scheduler doesn't try to place them into free slots or warn when the day's total minutes are too many.

This is reasonable for a pet owner because the tasks that truly can't move, like appointments and medication times, are the ones with fixed times. Flexible tasks can be squeezed in whenever the owner has a free moment, and automatically assigning them times would make the app guess at the owner's day. The owner still sees the total minutes for the day and can decide what fits.

**Readability vs. cleverness:** I asked my AI assistant how `detect_conflicts` could be simplified or made faster. It suggested a "sweep line": sort tasks by start time and only compare each task with the ones still running. That's faster for very large lists, but it's harder to read and easier to get wrong. A household has maybe 5 to 15 timed tasks a day, so checking every pair with `itertools.combinations` is instant. I kept the pairwise version because anyone can read it and see that it is correct. I did accept one simplification for sorting: `get_daily_tasks` now sorts by time with `sort_by_time()` and then by priority. Python's sort is stable, so that one line replaces a three-part sort key and reuses the new method.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used my AI coding assistant in each step: brainstorming the four classes and turning them into a Mermaid UML diagram, generating the dataclass skeleton, reviewing that skeleton for missing relationships and logic bottlenecks, filling in the method logic, writing the `main.py` demo with a readable table, drafting the first pytest tests, and adding docstrings.

The most helpful prompts were review questions about my own code, like "Attach pawpal_system.py: do you notice any missing relationships or potential logic bottlenecks?" Those found real design bugs (listed in 1b), such as a single `completed` flag marking a daily task done for every day. Specific requests also worked well, like asking for "a clearer, more readable way to format this schedule output for the terminal."

**AI strategy**

- **Most effective features:** agent mode that could edit several files at once was the biggest help. The recurring-task change touched `pawpal_system.py`, `main.py`, the tests, and the README together, and the assistant kept them consistent. It also ran `python main.py` and `python -m pytest` itself after each change, so I saw real output instead of guesses. Attaching a file and asking a review question ("any missing relationships or bottlenecks?") was the most valuable chat feature.
- **A suggestion I rejected or modified to keep the design clean:** the starter `app.py` stored tasks as plain dictionaries in `st.session_state.tasks`. Keeping that pattern would have meant two separate task models, the dictionaries in the UI and the `Task` class in the logic layer. Instead I stored a single `Owner` object in `st.session_state` and made every form and table go through `Owner`, `Pet`, and `Scheduler` methods, so the UI has no scheduling logic of its own. I also turned down the AI's faster "sweep line" conflict check in favor of the simpler pairwise version (see 2b).
- **Organizing by phase:** I worked one phase at a time and gave the assistant only that phase's instructions. Keeping each session focused on one goal (design, then core logic, then UI, then algorithms, then testing) meant the AI's answers stayed on topic, I could check each phase was complete before moving on, and each phase ended with its own commit, so the git history reads like the project plan.
- **Being the lead architect:** the AI was fast at writing code, but I had to own the decisions. That meant choosing which constraints matter, rejecting extra complexity, and checking that a change in one class didn't quietly break another. The AI was also confident about everything, so my job was to ask "why?", read what it wrote, and insist on proof: a passing test or a printed schedule.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

**What AI suggested and what I accepted:** I accepted the six skeleton-review changes in 1b because each one fixed a concrete problem I could explain myself, like a `date` field shadowing Python's `date` type, or titles not being unique after a reschedule.

**What I did not accept as-is:** The review pointed out that the weekly calendar repeats the daily lookup 7 times and conflict detection compares every pair of tasks, which could be optimized. I kept the simple versions because one household only has a handful of pet tasks, and simpler code is easier to read and test. The AI also noted that my daily list sorts by priority first, so a 2:30 PM High task prints before a 2:00 PM Medium task. I kept priority-first ordering on purpose, because the owner should see the most important tasks at the top.

**How I verified it:** after each phase I ran `main.py` and checked the printed schedule by hand: both pets' tasks combined, sorted High > Medium > Low, the correct total minutes, today's walk marked done with tomorrow's walk created, and the same-time breakfasts and vet/flea-medicine overlap flagged. I ran `python -m pytest` after every change; the suite grew from 2 tests to 24, all passing. For the Streamlit app, I clicked through the full workflow (add pets, add tasks, filter, sort, mark done) to confirm the UI actually calls the scheduler and keeps data between reruns.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The 24 tests in `tests/test_pawpal.py` cover five areas:

- **Sorting:** clock order with "Anytime" tasks last, ties keeping their original order, and the daily list ordered by priority and then time.
- **Filtering:** by pet, by done/not-done, and by both.
- **Recurring tasks:** Daily creates the next day's task, Weekly creates one 7 days later, Once creates nothing. Completing twice doesn't duplicate, a chain of daily completions shows exactly one walk per day, and a weekly task appears only once in a 7-day calendar.
- **Conflicts:** exact same-time tasks (including across different pets), and no false alarms for tasks that only touch end to end, "Anytime" tasks, or tasks on other days.
- **Edge cases:** an owner with no pets, a pet with no tasks, completing a task on the wrong day or one that belongs to no pet, rescheduling one occurrence, and rejecting invalid priority, frequency, or duration values.

These tests matter because the scheduling logic has subtle rules that are easy to break without noticing. The recurring-task change in Phase 4 is a good example: if completing a daily walk created a duplicate, or marked every future walk done, the schedule would look almost right but be wrong. Tests catch that instantly, and they let me refactor (like simplifying the sort) with confidence.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm fairly confident, about 4.5 out of 5. Every scheduling feature has tests, including its main edge cases, and all 24 pass. The CLI demo and a full click-through of the Streamlit app match what the tests expect. I'm not at 5 because the UI is only tested by hand.

Next I would test:

- tasks that run past midnight (an 11:30 PM task that lasts 60 minutes)
- an overdue recurring task that was never completed, which keeps showing on later days
- rescheduling a task onto a day that already has a conflict
- a weekly task whose due date is in the middle of the 7-day calendar
- automated tests for `app.py` using Streamlit's `AppTest`

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the recurring-task design. Each `Task` is one occurrence, and completing a Daily or Weekly task creates the next one with `timedelta`. That keeps "done" and "to do" simple, works the same in the CLI and the UI, and is backed by tests for the tricky cases (completing twice, completing a later day early, chains of completions). I'm also happy that the UI has no logic of its own: every table, filter, and warning comes from a `Scheduler` method, so the CLI demo and the app always agree.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

- **Save data between sessions:** right now everything lives in `st.session_state`, so closing the browser loses it. I would save the owner's pets and tasks to a JSON file or a small database.
- **Editing and deleting from the UI:** `Pet.remove_task` and `Pet.reschedule_task` exist in the logic layer, but the app doesn't offer them yet.
- **Smarter planning for "Anytime" tasks:** suggest open time slots for flexible tasks, and warn when the day's total minutes exceed the time the owner says they have.
- **Overdue tasks:** show missed recurring tasks clearly instead of letting an uncompleted daily task keep appearing.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Designing first made everything after it easier. Because the UML set clear jobs for each class (Task knows about itself, Pet owns its tasks, Owner gathers them, Scheduler organizes them), every new feature had an obvious home, and the AI's code fit into that structure instead of sprawling. The bigger lesson about AI is that it speeds up writing code, but it doesn't own the design. I had to stay the lead architect: decide what the system should do, keep it simple, and verify every change with tests and real output before trusting it.
