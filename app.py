import streamlit as st
from datetime import date, time

from pawpal_system import FREQUENCIES, PRIORITIES, Owner, Pet, Scheduler, Task

CATEGORIES = ["walk", "feeding", "meds", "grooming", "appointment", "other"]
PRIORITY_ICONS = {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}


def time_label(task: Task) -> str:
    """Return a task's start time as '07:30 AM', or 'Anytime' if it has none."""
    return task.start_time.strftime("%I:%M %p") if task.start_time else "Anytime"


def task_rows(tasks: list[Task], day: date) -> list[dict]:
    """Turn tasks into table rows for st.table."""
    return [{"Done": "✅" if t.is_completed_on(day) else "⬜",
             "Time": time_label(t),
             "Task": t.title,
             "Pet": t.pet_name,
             "Minutes": t.duration_minutes,
             "Priority": PRIORITY_ICONS[t.priority],
             "Repeats": t.frequency}
            for t in tasks]


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' daily care: feedings, walks, meds, and appointments.")

# Streamlit reruns this script on every click, so keep the Owner in session_state.
# Only create it the first time; after that, reuse the same object.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)

owner.name = st.text_input("Owner name", value=owner.name)

# Show a message saved before st.rerun() (e.g. after marking a task done).
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

st.divider()

# --- Add a pet -------------------------------------------------------------
st.subheader("1. Pets")

with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["Dog", "Cat", "Other"])
    with col3:
        age = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        name = pet_name.strip()
        if not name:
            st.error("Please enter a pet name.")
        elif any(p.name == name for p in owner.pets):
            st.error(f"You already have a pet named {name}.")
        else:
            owner.add_pet(Pet(name, species, int(age)))
            st.success(f"Added {name}!")

if owner.pets:
    st.table([{"Name": p.name, "Species": p.species, "Age": p.age} for p in owner.pets])
else:
    st.info("No pets yet. Add one above to get started.")

st.divider()

# --- Add a task ------------------------------------------------------------
st.subheader("2. Tasks")

if not owner.pets:
    st.info("Add a pet before scheduling tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        pet_choice = st.selectbox("Pet", [p.name for p in owner.pets])
        col1, col2 = st.columns(2)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
            category = st.selectbox("Category", CATEGORIES)
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=20)
        with col2:
            priority = st.selectbox("Priority", PRIORITIES)
            frequency = st.selectbox("Repeats", FREQUENCIES)
            due_date = st.date_input("Date (first day, if repeating)", value=date.today())
        has_time = st.checkbox("Happens at a fixed time (e.g. vet appointment, medication)")
        start_time = st.time_input("Start time", value=time(9, 0))

        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == pet_choice)
            try:
                task = Task(task_title.strip() or "Untitled task", category, int(duration), priority,
                            due_date, frequency, start_time if has_time else None)
            except ValueError as err:
                st.error(str(err))
            else:
                pet.add_task(task)
                st.success(f"Added '{task.title}' for {pet.name}.")

st.divider()

# --- Schedule --------------------------------------------------------------
st.subheader("3. Schedule")

day = st.date_input("Show schedule for", value=date.today(), key="schedule_day")
day_tasks = scheduler.get_daily_tasks(day)

if not day_tasks:
    st.info(f"Nothing scheduled for {day:%A, %b %d}.")
else:
    # Conflicts go first so the owner sees them before planning the day.
    conflicts = scheduler.get_conflict_warnings(day)
    if conflicts:
        label = "time conflict" if len(conflicts) == 1 else "time conflicts"
        st.warning(f"**{len(conflicts)} {label}** on {day:%A, %b %d}. "
                   "You can't be in two places at once, so consider moving one task in each pair:\n\n"
                   + "\n".join(f"- {c}" for c in conflicts))
    else:
        st.success("No time conflicts. Every fixed-time task has its own slot.")

    open_tasks = scheduler.filter_tasks(day, completed=False)
    done_count = len(day_tasks) - len(open_tasks)
    col1, col2, col3 = st.columns(3)
    col1.metric("Tasks", len(day_tasks))
    col2.metric("Done", f"{done_count} / {len(day_tasks)}")
    col3.metric("Total time", f"{scheduler.total_duration(day)} min")

    # Filters and sort order, all handled by Scheduler methods.
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_mode = st.radio("Sort by", ["Priority", "Time of day"],
                             help="Priority: High > Medium > Low, fixed times first. "
                                  "Time of day: clock order, 'Anytime' tasks last.")
    with col2:
        pet_filter = st.selectbox("Pet", ["All pets"] + [p.name for p in owner.pets])
    with col3:
        status_filter = st.selectbox("Status", ["All", "To do", "Done"])

    shown = scheduler.filter_tasks(
        day,
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "To do": False, "Done": True}[status_filter],
    )
    if sort_mode == "Time of day":
        shown = scheduler.sort_by_time(shown)

    if shown:
        st.table(task_rows(shown, day))
    else:
        st.info("No tasks match these filters.")

    # Mark a task done; recurring tasks create their next occurrence.
    if open_tasks:
        with st.form("mark_done"):
            choice = st.selectbox("Mark a task done", range(len(open_tasks)),
                                  format_func=lambda i: f"{time_label(open_tasks[i])} - "
                                                        f"{open_tasks[i].title} ({open_tasks[i].pet_name})")
            if st.form_submit_button("✅ Mark done"):
                task = open_tasks[choice]
                next_task = scheduler.mark_task_complete(task, day)
                message = f"Marked '{task.title}' for {task.pet_name} done."
                if next_task is not None:
                    message += f" Next {task.frequency.lower()} occurrence added for {next_task.due_date:%A, %b %d}."
                st.session_state.flash = message
                st.rerun()
    else:
        st.success("🎉 Every task for this day is done!")

# --- Week ------------------------------------------------------------------
with st.expander("📅 7-day overview"):
    week = scheduler.get_weekly_calendar(day)
    st.table([{"Day": f"{d:%a %b %d}",
               "Tasks": len(tasks),
               "Minutes": sum(t.duration_minutes for t in tasks),
               "Conflicts": len(scheduler.detect_conflicts(d)) or "",
               "What's planned": ", ".join(f"{t.title} ({t.pet_name})" for t in tasks) or "-"}
              for d, tasks in week.items()])
