from datetime import date, time

import streamlit as st

from pawpal_system import CareTask, Owner, Pet, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to PawPal+, a pet care planning assistant. Set up your owner and pet,
add a few care tasks, then generate a schedule for the day.
"""
)

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

# Map the UI's lowercase priority strings to the Priority enum.
PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}
CATEGORIES = ["exercise", "feeding", "grooming", "training", "other"]

# --- Session state: create the Owner once, then reuse it on every rerun. ---
# Streamlit reruns this whole script on each interaction, so a plain
# `owner = Owner(...)` would be wiped out every click. Stashing it in the
# session_state "vault" lets pets and tasks persist across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)

owner = st.session_state.owner

st.divider()

st.subheader("Owner & Pet")

col_a, col_b = st.columns(2)
with col_a:
    owner.name = st.text_input("Owner name", value=owner.name)
    owner.available_minutes = st.number_input(
        "Available minutes today", min_value=1, max_value=1440,
        value=owner.available_minutes,
    )
with col_b:
    owner.preferences = st.multiselect(
        "Preferred categories", CATEGORIES, default=owner.preferences,
        help="Tasks in these categories get scheduled sooner.",
    )

st.markdown("#### Add a pet")
col_c, col_d, col_e, col_f = st.columns(4)
with col_c:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_d:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col_e:
    breed = st.text_input("Breed", value="Mixed")
with col_f:
    pet_age = st.number_input("Age", min_value=0, max_value=40, value=3)

if st.button("Add pet"):
    # Register the pet on the Owner via the backend method.
    owner.add_pet(Pet(name=pet_name, species=species, breed=breed, age=int(pet_age)))
    st.success(f"Added {pet_name}.")

if owner.pets:
    st.caption("Pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above before creating tasks.")

st.divider()

st.subheader("Add a Task")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5 = st.columns(2)
with col4:
    category = st.selectbox("Category", CATEGORIES)
with col5:
    # Pick which registered pet this task is for.
    pet_choice = st.selectbox(
        "For pet",
        options=owner.pets,
        format_func=lambda p: p.name,
        disabled=not owner.pets,
    )

if st.button("Add task", disabled=not owner.pets):
    task = CareTask(
        title=task_title,
        duration_minutes=int(duration),
        priority=PRIORITY_MAP[priority],
        category=category,
    )
    owner.add_task(task, pet=pet_choice)
    st.success(f"Added “{task_title}” for {pet_choice.name}.")

# Show the tasks currently held on the Owner (pending only).
pending = owner.all_tasks()
if pending:
    st.write("Current tasks:")
    st.table(
        [
            {
                "title": t.title,
                "pet": t.pet.name if t.pet else "—",
                "duration_minutes": t.duration_minutes,
                "priority": t.priority.name,
                "category": t.category,
            }
            for t in pending
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")

col_f, col_g = st.columns(2)
with col_f:
    start_hour = st.number_input("Start hour", min_value=0, max_value=23, value=8)
with col_g:
    start_minute = st.number_input("Start minute", min_value=0, max_value=59, value=0)

if st.button("Generate schedule"):
    if not pending:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.build_plan(
            tasks=owner.all_tasks(),
            start_time=time(int(start_hour), int(start_minute)),
            plan_date=date.today(),
        )
        st.text(plan.explain())

if st.button("Clear pets & tasks"):
    st.session_state.owner = Owner(
        name=owner.name,
        available_minutes=owner.available_minutes,
        preferences=owner.preferences,
    )
    st.rerun()
