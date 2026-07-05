"""PawPal+ — pet care planning assistant.

Class skeleton generated from diagrams/uml.mmd.
Dataclasses are used for plain data objects (Pet, CareTask, ScheduledItem);
behavior-heavy types (Owner, Scheduler, DailyPlan) are regular classes.
Method bodies are stubs to be filled in.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum


class Priority(Enum):
    """Task priority levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Pet:
    """A pet owned by an Owner."""

    name: str
    species: str
    breed: str
    age: int


@dataclass
class CareTask:
    """A single care task that may be scheduled."""

    title: str
    duration_minutes: int
    priority: Priority
    category: str
    recurring: bool = False
    completed: bool = False
    pet: "Pet | None" = None

    def priority_rank(self) -> int:
        """Return a numeric rank used for sorting tasks.

        Higher is more urgent, so the enum value maps directly
        (HIGH -> 3, MEDIUM -> 2, LOW -> 1). Sorting can then order
        tasks by descending rank.
        """
        return self.priority.value

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.completed = True


@dataclass
class ScheduledItem:
    """A CareTask placed at a specific time in a DailyPlan."""

    task: CareTask
    start_time: time
    end_time: time
    reason: str


class Owner:
    """The person managing pets and care tasks."""

    def __init__(self, name: str, available_minutes: int,
                 preferences: list[str] | None = None) -> None:
        """Create an owner with a name, daily time budget, and preferences."""
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences if preferences is not None else []
        self.pets: list[Pet] = []
        self.tasks: list[CareTask] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        if pet not in self.pets:
            self.pets.append(pet)

    def add_task(self, task: CareTask, pet: Pet | None = None) -> None:
        """Add a care task to this owner, optionally linked to a pet.

        If a pet is given it is auto-registered and attached to the task
        so the scheduler can report which pet each task belongs to.
        """
        if pet is not None:
            self.add_pet(pet)
            task.pet = pet
        self.tasks.append(task)

    def remove_task(self, task: CareTask) -> None:
        """Remove a care task from this owner (no error if absent)."""
        if task in self.tasks:
            self.tasks.remove(task)

    def all_tasks(self, include_completed: bool = False) -> list[CareTask]:
        """Return every task across all pets.

        By default completed tasks are excluded, since a day's plan only
        needs the work that still remains.
        """
        if include_completed:
            return list(self.tasks)
        return [task for task in self.tasks if not task.completed]

    def tasks_for(self, pet: Pet) -> list[CareTask]:
        """Return this owner's tasks that belong to a specific pet."""
        return [task for task in self.tasks if task.pet is pet]


class Scheduler:
    """Builds a daily plan from a set of care tasks."""

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler bound to the given owner."""
        self.owner = owner

    @property
    def available_minutes(self) -> int:
        """Available minutes, sourced from the owner."""
        return self.owner.available_minutes

    @property
    def preferences(self) -> list[str]:
        """Owner preferences that influence scheduling."""
        return self.owner.preferences

    def _preferred(self, task: CareTask) -> bool:
        """Whether a task matches one of the owner's stated preferences."""
        return task.category in self.preferences

    def sort_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Return tasks ordered by scheduling priority.

        Ordering, most important first:
          1. higher priority (HIGH > MEDIUM > LOW)
          2. tasks whose category the owner prefers
          3. shorter tasks (so more can fit in the day)
        The original list is left untouched.
        """
        return sorted(
            tasks,
            key=lambda t: (t.priority_rank(), self._preferred(t), -t.duration_minutes),
            reverse=True,
        )

    def filter_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Return the subset of tasks that fit the available time.

        Tasks are considered in the given order and greedily accepted
        while budget remains; a task too big for the leftover time is
        skipped (a later, shorter task may still fit).
        """
        remaining = self.available_minutes
        fitted: list[CareTask] = []
        for task in tasks:
            if task.duration_minutes <= remaining:
                fitted.append(task)
                remaining -= task.duration_minutes
        return fitted

    def build_plan(self, tasks: list[CareTask], start_time: time,
                   plan_date: date) -> "DailyPlan":
        """Assemble a DailyPlan from the given tasks.

        Tasks are sorted, then placed back-to-back starting at
        ``start_time``. Whatever does not fit the available minutes is
        recorded as skipped so the plan can explain the omission.
        """
        ordered = self.sort_tasks(tasks)
        plan = DailyPlan(plan_date=plan_date)

        cursor = datetime.combine(plan_date, start_time)
        remaining = self.available_minutes

        for task in ordered:
            if task.duration_minutes <= remaining:
                end = cursor + timedelta(minutes=task.duration_minutes)
                reason = f"{task.priority.name} priority"
                if self._preferred(task):
                    reason += ", matches a preference"
                reason += f"; {remaining} min were free"
                plan.items.append(
                    ScheduledItem(
                        task=task,
                        start_time=cursor.time(),
                        end_time=end.time(),
                        reason=reason,
                    )
                )
                cursor = end
                remaining -= task.duration_minutes
            else:
                plan.skipped.append(task)

        return plan


@dataclass
class DailyPlan:
    """The result of scheduling: placed items plus skipped tasks."""

    plan_date: date
    items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[CareTask] = field(default_factory=list)

    def total_minutes(self) -> int:
        """Return the total scheduled minutes across all items."""
        return sum(item.task.duration_minutes for item in self.items)

    def explain(self) -> str:
        """Return a human-readable explanation of the plan."""
        lines = [
            f"Plan for {self.plan_date.isoformat()} "
            f"({self.total_minutes()} min scheduled):"
        ]

        if self.items:
            for item in self.items:
                pet = item.task.pet.name if item.task.pet else "you"
                lines.append(
                    f"  {item.start_time:%H:%M}-{item.end_time:%H:%M}  "
                    f"{item.task.title} (for {pet}) — {item.reason}"
                )
        else:
            lines.append("  Nothing scheduled.")

        if self.skipped:
            lines.append("Skipped (no time left):")
            for task in self.skipped:
                lines.append(f"  - {task.title} ({task.duration_minutes} min)")

        return "\n".join(lines)
