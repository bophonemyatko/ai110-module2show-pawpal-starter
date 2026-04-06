import streamlit as st
from pawpal_system import Pet, Task, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("A smart daily planner for your pets' care tasks.")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan",
        free_minutes_per_day=120,
        preferences={"skip_weekends": False},
    )
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()

# ---------------------------------------------------------------------------
# Owner setup
# ---------------------------------------------------------------------------
st.subheader("Owner")
col_name, col_time, col_wknd = st.columns([2, 1, 1])
with col_name:
    owner_name = st.text_input("Owner name", value=st.session_state.owner.name)
with col_time:
    free_minutes = st.number_input(
        "Free minutes/day", min_value=10, max_value=480,
        value=st.session_state.owner.free_minutes_per_day,
    )
with col_wknd:
    skip_weekends = st.checkbox(
        "Skip weekends",
        value=st.session_state.owner.preferences.get("skip_weekends", False),
    )

# Keep owner in sync with form values
st.session_state.owner.name = owner_name
st.session_state.owner.free_minutes_per_day = int(free_minutes)
st.session_state.owner.preferences["skip_weekends"] = skip_weekends

# ---------------------------------------------------------------------------
# Add a Pet
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Pets")

with st.form("add_pet_form", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        pet_name = st.text_input("Pet name", value="Mochi")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
    with col3:
        st.write("")
        st.write("")
        add_pet_btn = st.form_submit_button("Add pet", use_container_width=True)

if add_pet_btn:
    existing_names = [p.name.lower() for p in st.session_state.owner.pets]
    if pet_name.strip().lower() in existing_names:
        st.warning(f"A pet named '{pet_name}' already exists.")
    else:
        new_pet = Pet(name=pet_name.strip(), species=species)
        st.session_state.owner.add_pet(new_pet)
        st.success(f"Added {new_pet.name} the {new_pet.species}.")

if st.session_state.owner.pets:
    st.table([
        {"Name": p.name, "Species": p.species, "Tasks": len(p.tasks)}
        for p in st.session_state.owner.pets
    ])
else:
    st.info("No pets yet — add one above.")

# ---------------------------------------------------------------------------
# Add a Task
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Add a Task")

if not st.session_state.owner.pets:
    st.warning("Add a pet first before adding tasks.")
else:
    pet_names = [p.name for p in st.session_state.owner.pets]

    with st.form("add_task_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            selected_pet_name = st.selectbox("Assign to pet", pet_names)
        with col3:
            priority = st.selectbox("Priority", ["high", "medium", "low"])

        col4, col5, col6, col7 = st.columns(4)
        with col4:
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col5:
            preferred_time = st.text_input("Preferred time (HH:MM)", value="")
        with col6:
            mandatory = st.checkbox("Mandatory")
        with col7:
            recurrence = st.selectbox("Recurrence", [None, "daily", "weekly"])

        add_task_btn = st.form_submit_button("Add task", use_container_width=True)

    if add_task_btn:
        try:
            selected_pet = next(
                p for p in st.session_state.owner.pets if p.name == selected_pet_name
            )
            task = Task(
                title=task_title.strip(),
                duration_minutes=int(duration),
                priority=priority,
                preferred_time=preferred_time.strip(),
                mandatory=mandatory,
                recurrence=recurrence,
            )
            selected_pet.add_task(task)
            st.success(f"'{task.title}' added to {selected_pet.name}.")
        except ValueError as e:
            st.error(str(e))

# ---------------------------------------------------------------------------
# All Tasks — sorted + filtered, with live conflict detection
# ---------------------------------------------------------------------------
st.divider()
st.subheader("All Tasks")

all_tasks = st.session_state.owner.get_all_tasks()

if not all_tasks:
    st.info("No tasks yet — add some above.")
else:
    scheduler = st.session_state.scheduler

    # --- Live conflict detection ---
    conflicts = scheduler._detect_conflicts(all_tasks)
    for warning in conflicts:
        st.warning(f"⚠️ {warning}")

    # --- Filters ---
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        pet_filter_options = ["All pets"] + [p.name for p in st.session_state.owner.pets]
        pet_filter = st.selectbox("Filter by pet", pet_filter_options, key="pet_filter")
    with filter_col2:
        status_filter = st.selectbox(
            "Filter by status", ["All", "incomplete", "in progress", "complete"],
            key="status_filter",
        )

    # Apply filters via Owner.filter_tasks()
    filtered_pet   = None if pet_filter == "All pets" else pet_filter
    filtered_status = None if status_filter == "All" else status_filter
    filtered_tasks = st.session_state.owner.filter_tasks(
        status=filtered_status, pet_name=filtered_pet
    )

    # Sort via Scheduler.sort_tasks()
    sorted_tasks = scheduler.sort_tasks(filtered_tasks)

    if not sorted_tasks:
        st.info("No tasks match the current filters.")
    else:
        PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        STATUS_ICON   = {"incomplete": "⬜", "in progress": "🔄", "complete": "✅"}

        # Table view of sorted tasks
        st.dataframe(
            [
                {
                    "Priority": f"{PRIORITY_ICON.get(t.priority, '')} {t.priority}",
                    "Task": ("🔒 " if t.mandatory else "") + t.title,
                    "Pet": t.pet.name if t.pet else "—",
                    "Duration": f"{t.duration_minutes} min",
                    "Preferred Time": t.preferred_time or "—",
                    "Recurrence": t.recurrence or "—",
                    "Status": f"{STATUS_ICON.get(t.status, '')} {t.status}",
                }
                for t in sorted_tasks
            ],
            use_container_width=True,
            hide_index=True,
        )

        # Per-task action buttons below the table
        st.caption("Task actions (sorted by scheduling priority — 🔒 = mandatory):")
        for i, t in enumerate(sorted_tasks):
            col_a, col_b, col_c = st.columns([4, 1, 1])
            with col_a:
                label = ("🔒 " if t.mandatory else "") + f"**{t.title}** — {t.pet.name if t.pet else '—'}"
                st.markdown(label)
            with col_b:
                if t.status == "incomplete" and st.button(
                    "In progress", key=f"prog_{i}", use_container_width=True
                ):
                    t.mark_in_progress()
                    st.rerun()
            with col_c:
                if t.status != "complete" and st.button(
                    "Complete", key=f"done_{i}", use_container_width=True
                ):
                    t.mark_complete()
                    st.rerun()

# ---------------------------------------------------------------------------
# Build Schedule
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Daily Schedule")
st.caption("Generates a priority-ordered plan within your free time budget.")

if st.button("Generate schedule", type="primary", use_container_width=True):
    planner = st.session_state.scheduler.generate_plan(st.session_state.owner)
    st.session_state.last_plan = planner

if "last_plan" in st.session_state:
    planner = st.session_state.last_plan

    # Metrics row
    m1, m2, m3 = st.columns(3)
    m1.metric("Tasks scheduled", len(planner.scheduled_tasks))
    m2.metric("Minutes used", planner.total_minutes)
    m3.metric("Minutes remaining", st.session_state.owner.free_minutes_per_day - planner.total_minutes)

    # Conflict / missed-slot warnings
    if planner.warnings:
        for w in planner.warnings:
            st.warning(f"⚠️ {w}")

    # Scheduled tasks table
    if planner.scheduled_tasks:
        st.success(f"Plan generated — {len(planner.scheduled_tasks)} task(s) scheduled.")
        st.dataframe(
            [
                {
                    "Start": s.start_time,
                    "End": s.end_time,
                    "Task": ("🔒 " if s.task.mandatory else "") + s.task.title,
                    "Pet": s.task.pet.name if s.task.pet else "—",
                    "Duration": f"{s.task.duration_minutes} min",
                    "Priority": s.task.priority,
                    "Reason": s.reason,
                }
                for s in planner.scheduled_tasks
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("No tasks could be scheduled. Check that tasks are added and fit within free time.")

    # Skipped tasks
    if planner.skipped_tasks:
        with st.expander(f"⏭️ {len(planner.skipped_tasks)} task(s) skipped — did not fit in time budget"):
            st.dataframe(
                [
                    {
                        "Task": t.title,
                        "Pet": t.pet.name if t.pet else "—",
                        "Duration": f"{t.duration_minutes} min",
                        "Priority": t.priority,
                        "Mandatory": "Yes" if t.mandatory else "No",
                    }
                    for t in planner.skipped_tasks
                ],
                use_container_width=True,
                hide_index=True,
            )
