"""Demo script for the PawPal+ pet care planner.

Creates an owner with a couple of pets, gives them some care tasks with
different durations/priorities, and prints out today's schedule.
"""

from datetime import date, time

from pawpal_system import CareTask, Owner, Pet, Priority, Scheduler


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

    # Add at least three tasks with different times to those pets.
    owner.add_task(
        CareTask(
            title="Morning walk",
            duration_minutes=45,
            priority=Priority.HIGH,
            category="exercise",
        ),
        pet=rex,
    )
    owner.add_task(
        CareTask(
            title="Feed breakfast",
            duration_minutes=15,
            priority=Priority.HIGH,
            category="feeding",
        ),
        pet=milo,
    )
    owner.add_task(
        CareTask(
            title="Brush coat",
            duration_minutes=20,
            priority=Priority.MEDIUM,
            category="grooming",
        ),
        pet=milo,
    )
    owner.add_task(
        CareTask(
            title="Play fetch",
            duration_minutes=30,
            priority=Priority.LOW,
            category="exercise",
        ),
        pet=rex,
    )

    # Build a plan for today, starting at 8:00 AM.
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan(
        tasks=owner.all_tasks(),
        start_time=time(8, 0),
        plan_date=date.today(),
    )

    print("Today's Schedule")
    print("=" * 40)
    print(plan.explain())


if __name__ == "__main__":
    main()
