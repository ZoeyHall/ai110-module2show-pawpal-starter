import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler, format_minutes, time_to_minutes

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

# Keep one Owner across reruns so pets and tasks are not lost on each click.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=60)
owner = st.session_state.owner
scheduler = Scheduler(owner)


def task_rows(tasks: list[Task]) -> list[dict]:
    """Turn tasks into table rows for display."""
    return [
        {
            "due": f"{t.due_date:%m/%d}",
            "time": t.time or "anytime",
            "task": t.description,
            "pet": t.pet_name,
            "minutes": t.duration_minutes,
            "priority": t.priority,
            "frequency": t.frequency,
            "status": "done" if t.completed else "to do",
        }
        for t in tasks
    ]


st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = int(
    st.number_input(
        "Minutes available today", min_value=0, max_value=1440, value=owner.available_minutes
    )
)

st.subheader("Add a Pet")
col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    age = st.number_input("Age", min_value=0, max_value=40, value=2)

if st.button("Add pet"):
    if not pet_name.strip():
        st.error("Please enter a pet name.")
    elif owner.get_pet(pet_name.strip()):
        st.error(f"{pet_name.strip()} is already added.")
    else:
        owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
        st.success(f"Added {pet_name.strip()}.")

if owner.pets:
    st.write("Your pets:")
    st.table([{"name": p.name, "species": p.species, "age": p.age} for p in owner.pets])
else:
    st.info("No pets yet. Add one above.")

st.subheader("Schedule a Task")
if not owner.pets:
    st.caption("Add a pet first, then you can add tasks for it.")
else:
    task_pet = st.selectbox("For which pet?", [p.name for p in owner.pets])
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task description", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    col4, col5 = st.columns(2)
    with col4:
        task_time = st.text_input("Time (HH:MM, optional)", value="")
    with col5:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])

    if st.button("Add task"):
        time_text = task_time.strip()
        start = time_to_minutes(time_text)
        if not task_title.strip():
            st.error("Please enter a task description.")
        elif time_text and start is None:
            st.error("Time must look like 08:30 (24-hour clock), or be left blank.")
        else:
            new_task = Task(
                description=task_title.strip(),
                duration_minutes=int(duration),
                priority=priority,
                # Store times zero-padded ("7:30" -> "07:30") so they display evenly.
                time=format_minutes(start) if start is not None else "",
                frequency=frequency,
            )
            owner.get_pet(task_pet).add_task(new_task)
            st.success(f"Added '{new_task.description}' for {task_pet}.")

            # Warn right away if the new task clashes with something due today.
            clashes = [
                w
                for w in scheduler.detect_conflicts(scheduler.get_pending_tasks())
                if f"'{new_task.description}'" in w
            ]
            for warning in clashes:
                st.warning(warning)

if owner.get_all_tasks():
    st.subheader("Your Tasks")
    col1, col2 = st.columns(2)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.selectbox("Show status", ["To do", "Done", "All"])

    shown = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"To do": False, "Done": True, "All": None}[status_filter],
    )
    shown = scheduler.sort_by_time(shown)

    if shown:
        st.caption("Sorted by time; tasks without a time are listed last.")
        st.table(task_rows(shown))
    else:
        st.info("No tasks match these filters.")

    pending = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    if pending:
        col1, col2 = st.columns([3, 1])
        with col1:
            to_complete = st.selectbox(
                "Mark a task complete",
                range(len(pending)),
                format_func=lambda i: (
                    f"{pending[i].description} for {pending[i].pet_name} "
                    f"(due {pending[i].due_date:%m/%d}"
                    f"{', ' + pending[i].time if pending[i].time else ''})"
                ),
            )
        with col2:
            st.write("")  # aligns the button with the select box
            if st.button("Complete"):
                task = pending[to_complete]
                next_task = scheduler.mark_task_complete(task)
                message = f"Completed '{task.description}'."
                if next_task:
                    message += (
                        f" Next {task.frequency} occurrence added for "
                        f"{next_task.due_date:%A, %m/%d}."
                    )
                # Keep the message across the rerun that refreshes the tables.
                st.session_state.flash = message
                st.rerun()

    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    plan = scheduler.generate_plan()

    if not plan and not scheduler.skipped:
        st.info("No pending tasks to schedule. Add some tasks above.")
    else:
        st.markdown(f"### Today's Schedule for {owner.name}")
        if plan:
            st.table(
                [
                    {
                        "time": t.time or "anytime",
                        "task": t.description,
                        "pet": t.pet_name,
                        "minutes": t.duration_minutes,
                        "priority": t.priority,
                    }
                    for t in plan
                ]
            )
        st.caption(
            f"{scheduler.total_scheduled_minutes()} of {owner.available_minutes} minutes used."
        )
        if scheduler.conflicts:
            st.error(f"⚠️ {len(scheduler.conflicts)} time conflict(s) in this plan:")
            for warning in scheduler.conflicts:
                st.warning(warning.removeprefix("Warning: "))
        else:
            st.success("No time conflicts in this plan.")

        if scheduler.skipped:
            st.warning(
                "Skipped (not enough time): "
                + ", ".join(f"{t.description} for {t.pet_name}" for t in scheduler.skipped)
            )
        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())
