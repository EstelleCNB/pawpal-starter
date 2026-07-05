"""Simple unit tests for the PawPal+ pet care planner."""

from pawpal_system import CareTask, Owner, Pet, Priority


def test_mark_done_changes_task_status():
    """Calling mark_done() flips a task's completed status to True."""
    task = CareTask(
        title="Morning walk",
        duration_minutes=45,
        priority=Priority.HIGH,
        category="exercise",
    )

    assert task.completed is False  # starts incomplete

    task.mark_done()

    assert task.completed is True  # status changed


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet increases that pet's task count."""
    owner = Owner(name="Caitlyn", available_minutes=120)
    rex = Pet(name="Rex", species="dog", breed="Labrador", age=4)

    assert len(owner.tasks_for(rex)) == 0  # no tasks yet

    owner.add_task(
        CareTask(
            title="Feed breakfast",
            duration_minutes=15,
            priority=Priority.HIGH,
            category="feeding",
        ),
        pet=rex,
    )

    assert len(owner.tasks_for(rex)) == 1  # count went up
