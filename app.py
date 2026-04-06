import streamlit as st
from pawpal_system import Pet, Task, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# --- Owner setup ---
st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
col_time, col_wknd = st.columns(2)
with col_time:
    free_minutes = st.number_input("Free minutes per day", min_value=10, max_value=480, value=120)
with col_wknd:
    skip_weekends = st.checkbox("Skip non-mandatory tasks on weekends", value=False)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name=owner_name,
        free_minutes_per_day=int(free_minutes),
        preferences={"skip_weekends": skip_weekends},
    )

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

# --- Add a Pet ---
st.divider()
st.subheader("Add a Pet")

col1, col2 = st.columns(2)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    new_pet = Pet(name=pet_name, species=species)
    st.session_state.owner.add_pet(new_pet)
    st.success(f"Added {new_pet.name} the {new_pet.species}.")

if st.session_state.owner.pets:
    st.write("Your pets:")
    st.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)} for p in st.session_state.owner.pets])
else:
    st.info("No pets yet. Add one above.")

# --- Add a Task ---
st.divider()
st.subheader("Add a Task")

if not st.session_state.owner.pets:
    st.warning("Add a pet first before scheduling tasks.")
else:
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet_name = st.selectbox("Assign task to", pet_names)
    selected_pet = next(p for p in st.session_state.owner.pets if p.name == selected_pet_name)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5, col6 = st.columns(3)
    with col4:
        preferred_time = st.text_input("Preferred time (e.g. 08:00)", value="")
    with col5:
        mandatory = st.checkbox("Mandatory task")
    with col6:
        recurrence = st.selectbox("Recurrence", [None, "daily", "weekly"])

    if st.button("Add task"):
        try:
            task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                preferred_time=preferred_time,
                mandatory=mandatory,
                recurrence=recurrence,
            )
            selected_pet.add_task(task)
            st.success(f"Task '{task.title}' added to {selected_pet.name}.")
        except ValueError as e:
            st.error(str(e))

    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        st.write("All tasks:")
        for i, t in enumerate(all_tasks):
            col_a, col_b, col_c = st.columns([3, 2, 2])
            with col_a:
                st.write(f"**{t.title}** ({t.pet.name if t.pet else '—'}) — {t.priority}, {t.duration_minutes}min")
            with col_b:
                st.write(f"Status: `{t.status}`")
            with col_c:
                if t.status != "complete" and st.button("Mark complete", key=f"complete_{i}"):
                    t.mark_complete()
                    st.rerun()
                elif t.status == "incomplete" and st.button("In progress", key=f"progress_{i}"):
                    t.mark_in_progress()
                    st.rerun()
    else:
        st.info("No tasks yet. Add one above.")

# --- Build Schedule ---
st.divider()
st.subheader("Build Schedule")
st.caption("Generates a daily plan from all pets' tasks within the owner's free time.")

if st.button("Generate schedule"):
    owner = st.session_state.owner
    owner.free_minutes_per_day = int(free_minutes)
    owner.preferences["skip_weekends"] = skip_weekends

    planner = st.session_state.scheduler.generate_plan(owner)

    if planner.scheduled_tasks:
        st.success(f"Scheduled {len(planner.scheduled_tasks)} task(s) using {planner.total_minutes} minutes.")
        st.table([
            {
                "task": scheduled.task.title,
                "pet": scheduled.task.pet.name if scheduled.task.pet else "—",
                "start": scheduled.start_time,
                "end": scheduled.end_time,
                "reason": scheduled.reason,
            }
            for scheduled in planner.scheduled_tasks
        ])
    else:
        st.warning("No tasks could be scheduled. Check that tasks are added and fit within free time.")

    if planner.warnings:
        for w in planner.warnings:
            st.warning(f"⚠ {w}")

    if planner.skipped_tasks:
        st.warning(f"{len(planner.skipped_tasks)} task(s) skipped — did not fit in the time budget:")
        st.table([
            {
                "task": t.title,
                "pet": t.pet.name if t.pet else "—",
                "duration (min)": t.duration_minutes,
                "priority": t.priority,
            }
            for t in planner.skipped_tasks
        ])
