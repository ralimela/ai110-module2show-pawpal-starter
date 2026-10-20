import streamlit as st
from datetime import date, time

from pawpal_system import FREQUENCIES, PRIORITIES, Owner, Pet, Scheduler, Task

CATEGORIES = ["walk", "feeding", "meds", "grooming", "appointment", "other"]

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' daily care: feedings, walks, meds, and appointments.")

# Streamlit reruns this script on every click, so keep the Owner in session_state.
# Only create it the first time; after that, reuse the same object.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
owner: Owner = st.session_state.owner

owner.name = st.text_input("Owner name", value=owner.name)

st.divider()

# --- Add a pet -------------------------------------------------------------
st.subheader("Pets")

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
    st.table([{"Name": p.name, "Species": p.species, "Age": p.age}
              for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Add a task ------------------------------------------------------------
st.subheader("Tasks")

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
        has_time = st.checkbox("Happens at a fixed time (e.g. vet appointment)")
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

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.table([{"Pet": t.pet_name, "Task": t.title, "Category": t.category,
                   "Minutes": t.duration_minutes, "Priority": t.priority,
                   "Repeats": t.frequency, "Starts": t.due_date.isoformat(),
                   "Time": t.start_time.strftime("%I:%M %p") if t.start_time else "Anytime"}
                  for t in all_tasks])

st.divider()

# --- Schedule --------------------------------------------------------------
st.subheader("Schedule")

scheduler = Scheduler(owner)
day = st.date_input("Show schedule for", value=date.today(), key="schedule_day")
daily = scheduler.get_daily_tasks(day)

if not daily:
    st.info("No tasks on this day.")
else:
    st.caption("Sorted High > Medium > Low; fixed-time tasks first within each priority.")
    st.table([{"Done": "✅" if t.is_completed_on(day) else "",
               "Time": t.start_time.strftime("%I:%M %p") if t.start_time else "Anytime",
               "Task": t.title, "Pet": t.pet_name,
               "Minutes": t.duration_minutes, "Priority": t.priority}
              for t in daily])
    st.metric("Total time", f"{scheduler.total_duration(day)} min")

    for warning in scheduler.get_conflict_warnings(day):
        st.warning(warning)
