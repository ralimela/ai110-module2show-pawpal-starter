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

The review also checked performance. The weekly calendar runs the daily lookup 7 times, and conflict detection compares tasks in pairs. Both are fine at the size of a household's pet tasks, so I kept them simple.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
