import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

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
        valid_time = (
            time_text == ""
            or (len(time_text) == 5 and time_text[2] == ":"
                and time_text[:2].isdigit() and time_text[3:].isdigit()
                and int(time_text[:2]) < 24 and int(time_text[3:]) < 60)
        )
        if not task_title.strip():
            st.error("Please enter a task description.")
        elif not valid_time:
            st.error("Time must look like 08:30, or be left blank.")
        else:
            owner.get_pet(task_pet).add_task(
                Task(
                    description=task_title.strip(),
                    duration_minutes=int(duration),
                    priority=priority,
                    time=time_text,
                    frequency=frequency,
                )
            )
            st.success(f"Added '{task_title.strip()}' for {task_pet}.")

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "pet": t.pet_name,
                "task": t.description,
                "time": t.time or "any",
                "minutes": t.duration_minutes,
                "priority": t.priority,
                "frequency": t.frequency,
            }
            for t in all_tasks
        ]
    )

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
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
        if scheduler.skipped:
            st.warning(
                "Skipped (not enough time): "
                + ", ".join(f"{t.description} for {t.pet_name}" for t in scheduler.skipped)
            )
        with st.expander("Why this plan?"):
            st.text(scheduler.explain_plan())
