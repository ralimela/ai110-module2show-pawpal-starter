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

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

**What AI suggested and what I accepted:** I accepted the six skeleton-review changes in 1b because each one fixed a concrete problem I could explain myself, like a `date` field shadowing Python's `date` type, or titles not being unique after a reschedule.

**What I did not accept as-is:** The review pointed out that the weekly calendar repeats the daily lookup 7 times and conflict detection compares every pair of tasks, which could be optimized. I kept the simple versions because one household only has a handful of pet tasks, and simpler code is easier to read and test. The AI also noted that my daily list sorts by priority first, so a 2:30 PM High task prints before a 2:00 PM Medium task. I kept priority-first ordering on purpose, because the owner should see the most important tasks at the top.

**How I verified it:** I ran `main.py` and checked the printed schedule by hand: two pets' tasks combined, sorted High > Medium > Low, the total of 140 minutes, and the vet/flea-medicine overlap flagged. I also ran `python -m pytest` and both tests passed (marking a task complete changes its status; adding a task increases the pet's task count).

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
