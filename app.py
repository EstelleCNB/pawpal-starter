from datetime import date, time

import streamlit as st

from pawpal_system import CareTask, Owner, Pet, Priority, Recurrence, Scheduler

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

# Map the UI's recurrence labels to the Recurrence enum. Recurring tasks
# regenerate their next occurrence when marked done (see "Mark a task done").
RECURRENCE_MAP = {
    "One-off": Recurrence.NONE,
    "Daily": Recurrence.DAILY,
    "Weekly": Recurrence.WEEKLY,
}

# Colored dots make priority scannable at a glance in the tables below.
PRIORITY_BADGE = {
    Priority.HIGH: "🔴 High",
    Priority.MEDIUM: "🟡 Medium",
    Priority.LOW: "⚪ Low",
}

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

col6, col7, col8 = st.columns(3)
with col6:
    # Anchor a task to a specific time of day (e.g. feed breakfast at 08:00).
    # Left off, the task floats and the scheduler packs it wherever it fits.
    anchor = st.checkbox(
        "Click to schedule to a specific time",
        help="Otherwise the scheduler places the task wherever it best fits.",
    )
with col7:
    anchor_time = st.time_input(
        "Preferred time", value=time(8, 0), disabled=not anchor
    )
with col8:
    # Recurring tasks (e.g. daily feeding) respawn their next occurrence when
    # completed, so essential care never silently drops off the list.
    recurrence_label = st.selectbox(
        "Repeats", list(RECURRENCE_MAP),
        help="Daily/weekly tasks auto-create their next occurrence when marked done.",
    )

if st.button("Add task", disabled=not owner.pets):
    recurrence = RECURRENCE_MAP[recurrence_label]
    task = CareTask(
        title=task_title,
        duration_minutes=int(duration),
        priority=PRIORITY_MAP[priority],
        category=category,
        preferred_time=anchor_time if anchor else None,
        recurrence=recurrence,
        # A recurring task needs a due date so its next occurrence can be
        # dated one step ahead; one-off tasks stay undated.
        due_date=date.today() if recurrence is not Recurrence.NONE else None,
    )
    owner.add_task(task, pet=pet_choice)
    st.success(f"Added “{task_title}” for {pet_choice.name}.")

# Show the tasks currently held on the Owner (pending only). A Scheduler
# instance drives the display so the same ordering/conflict/filter logic that
# builds the plan is what the user sees here.
scheduler = Scheduler(owner)
pending = owner.all_tasks()
if pending:
    st.markdown("#### Current tasks")

    # Optional per-pet filter, powered by the backend's filter_by().
    pet_names = [p.name for p in owner.pets]
    choice = st.selectbox("Filter by pet", ["All pets", *pet_names])
    shown = (
        pending
        if choice == "All pets"
        else scheduler.filter_by(pending, pet_name=choice)
    )

    # At-a-glance summary of the (filtered) task set.
    anchored_count = sum(1 for t in shown if t.preferred_time is not None)
    m1, m2, m3 = st.columns(3)
    m1.metric("Tasks", len(shown))
    m2.metric("Total minutes", sum(t.duration_minutes for t in shown))
    m3.metric("Anchored", anchored_count)

    if shown:
        # Order anchored tasks chronologically (floating tasks sort to the end),
        # mirroring how they'll be laid out on the timeline.
        st.table(
            [
                {
                    "Task": t.title,
                    "Pet": t.pet.name if t.pet else "—",
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": PRIORITY_BADGE[t.priority],
                    "Category": t.category.title(),
                    "Time": (
                        f"🕒 {t.preferred_time:%H:%M}"
                        if t.preferred_time
                        else "flexible"
                    ),
                    "Repeats": (
                        f"🔁 {t.recurrence.name.title()}"
                        if t.recurring
                        else "once"
                    ),
                }
                for t in scheduler.sort_by_time(shown)
            ]
        )
    else:
        st.info(f"No tasks for {choice}.")

    # Surface overlapping anchored tasks up front, before the user builds a plan.
    conflicts = scheduler.detect_conflicts(pending)
    if conflicts:
        st.warning(f"⚠️ {len(conflicts)} scheduling conflict(s) detected:")
        for warning in conflicts:
            st.warning(warning)
    else:
        st.success("✓ No scheduling conflicts.")

    # Complete a task. For a recurring task this fires the backend's
    # complete_task(), which marks it done and auto-creates the next
    # occurrence (due date advanced, completed reset) on the owner.
    st.markdown("#### Mark a task done")
    done_choice = st.selectbox(
        "Task to complete",
        options=pending,
        format_func=lambda t: (
            f"{t.title} — {t.pet.name if t.pet else '—'}"
            f"{' 🔁' if t.recurring else ''}"
        ),
    )
    if st.button("Mark done"):
        follow_up = scheduler.complete_task(done_choice)
        if follow_up is not None:
            st.success(
                f"✓ Completed “{done_choice.title}”. Next occurrence auto-created "
                f"for {follow_up.due_date.isoformat()} "
                f"(completed={follow_up.completed})."
            )
        else:
            st.success(f"✓ Completed “{done_choice.title}” (one-off, no repeat).")
        st.rerun()
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
        for warning in scheduler.detect_conflicts(pending):
            st.warning(warning)
        plan = scheduler.build_plan(
            tasks=owner.all_tasks(),
            start_time=time(int(start_hour), int(start_minute)),
            plan_date=date.today(),
        )

        st.success(f"Schedule ready for {plan.plan_date.isoformat()}.")

        # Headline numbers first.
        s1, s2, s3 = st.columns(3)
        s1.metric("Scheduled", f"{plan.total_minutes()} min")
        s2.metric("Free", f"{plan.unused_minutes} min")
        s3.metric("Tasks placed", len(plan.items))

        if plan.items:
            st.table(
                [
                    {
                        "Time": f"{item.start_time:%H:%M}–{item.end_time:%H:%M}",
                        "Task": item.task.title,
                        "Pet": item.task.pet.name if item.task.pet else "you",
                        "Priority": PRIORITY_BADGE[item.task.priority],
                        "Why": item.reason,
                    }
                    for item in plan.items
                ]
            )
        else:
            st.info("Nothing could be scheduled with the current time budget.")

        # Anything that didn't make the cut, with the backend's advice.
        if plan.skipped:
            st.warning(f"Skipped {len(plan.skipped)} task(s) — not enough time:")
            for task in plan.skipped:
                deficit = max(0, task.duration_minutes - plan.unused_minutes)
                note = (
                    f" (need {deficit} more min)" if deficit > 0 else ""
                )
                st.write(f"- **{task.title}** ({task.duration_minutes} min){note}")

        # Keep the raw text explanation available without cluttering the view.
        with st.expander("Plan details (text)"):
            st.text(plan.explain())

if st.button("Clear pets & tasks"):
    st.session_state.owner = Owner(
        name=owner.name,
        available_minutes=owner.available_minutes,
        preferences=owner.preferences,
    )
    st.rerun()
