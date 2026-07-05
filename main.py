"""Demo script for the PawPal+ pet care planner.

Creates an owner with a couple of pets, adds care tasks *out of order*, then
exercises the scheduler's sorting and filtering helpers before printing
today's schedule.
"""

from datetime import date, time

from pawpal_system import CareTask, Owner, Pet, Priority, Recurrence, Scheduler


def main() -> None:
    # An owner with two hours (120 minutes) of free time today.
    owner = Owner(
        name="Caitlyn",
        available_minutes=120,
        preferences=["exercise"],
    )

    # At least two pets.
    rex = Pet(name="Rex", species="dog", breed="Labrador", age=4)
    milo = Pet(name="Milo", species="cat", breed="Tabby", age=2)

    # Add tasks deliberately OUT OF chronological order so sort_by_time has
    # something real to reorder. Their preferred_time anchors jump around the
    # day (12:00, 07:30, 15:00, 08:00, 18:00).
    owner.add_task(
        CareTask(
            title="Play fetch",
            duration_minutes=30,
            priority=Priority.LOW,
            category="exercise",
            preferred_time=time(12, 0),
        ),
        pet=rex,
    )
    owner.add_task(
        CareTask(
            title="Feed breakfast",
            duration_minutes=15,
            priority=Priority.HIGH,
            category="feeding",
            recurrence=Recurrence.DAILY,  # essential; respawns each day
            preferred_time=time(7, 30),
            due_date=date.today(),
        ),
        pet=milo,
    )
    owner.add_task(
        CareTask(
            title="Brush coat",
            duration_minutes=20,
            priority=Priority.MEDIUM,
            category="grooming",
            preferred_time=time(15, 0),
        ),
        pet=milo,
    )
    owner.add_task(
        CareTask(
            title="Morning walk",
            duration_minutes=45,
            priority=Priority.HIGH,
            category="exercise",
            preferred_time=time(8, 0),
        ),
        pet=rex,
    )
    owner.add_task(
        CareTask(
            title="Feed dinner",
            duration_minutes=15,
            priority=Priority.HIGH,
            category="feeding",
            recurrence=Recurrence.DAILY,
            preferred_time=time(18, 0),
            due_date=date.today(),
        ),
        pet=milo,
    )
    # Deliberate clash: Rex's vet call is anchored at 08:00 — the same time as
    # his morning walk — so the two 08:00 tasks overlap and should be flagged.
    owner.add_task(
        CareTask(
            title="Vet phone call",
            duration_minutes=20,
            priority=Priority.MEDIUM,
            category="health",
            preferred_time=time(8, 0),
        ),
        pet=rex,
    )

    scheduler = Scheduler(owner)

    # --- Conflict detection: warn (don't crash) on overlapping anchored tasks.
    print("Conflict Detection")
    print("=" * 40)
    conflicts = scheduler.detect_conflicts(owner.all_tasks())
    if conflicts:
        for warning in conflicts:
            print(f"  ⚠ {warning}")
    else:
        print("  No scheduling conflicts detected.")
    print()

    # Complete the recurring breakfast. Because it's a DAILY task, the
    # scheduler automatically spawns tomorrow's occurrence.
    breakfast = next(t for t in owner.all_tasks() if t.title == "Feed breakfast")
    follow_up = scheduler.complete_task(breakfast)

    print("Recurrence")
    print("=" * 40)
    print(f"  Completed: {breakfast.title} (due {breakfast.due_date})")
    if follow_up is not None:
        print(f"  Auto-created next occurrence: {follow_up.title} "
              f"(due {follow_up.due_date}, completed={follow_up.completed})")
    print()

    # --- Sorting: tasks were added out of order; sort them by time of day. ---
    print("Tasks sorted by time (added out of order)")
    print("=" * 40)
    for task in scheduler.sort_by_time(owner.all_tasks(include_completed=True)):
        when = f"{task.preferred_time:%H:%M}" if task.preferred_time else "  —  "
        print(f"  {when}  {task.title} (for {task.pet.name})")

    # --- Filtering: by completion status, then by pet name. ---
    print("\nFiltering")
    print("=" * 40)
    all_tasks = owner.all_tasks(include_completed=True)
    outstanding = scheduler.filter_by(all_tasks, completed=False)
    finished = scheduler.filter_by(all_tasks, completed=True)
    milos = scheduler.filter_by(all_tasks, pet_name="Milo")

    print("  Outstanding:", [t.title for t in outstanding])
    print("  Completed:  ", [t.title for t in finished])
    print("  For Milo:   ", [t.title for t in milos])

    # --- Build a plan for today, starting at 8:00 AM. ---
    plan = scheduler.build_plan(
        tasks=owner.all_tasks(),
        start_time=time(8, 0),
        plan_date=date.today(),
    )

    print("\nToday's Schedule")
    print("=" * 40)
    print(plan.explain())


if __name__ == "__main__":
    main()
