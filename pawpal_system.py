"""PawPal+ — pet care planning assistant.

Class skeleton generated from diagrams/uml.mmd.
Dataclasses are used for plain data objects (Pet, CareTask, ScheduledItem);
behavior-heavy types (Owner, Scheduler, DailyPlan) are regular classes.
Method bodies are stubs to be filled in.
"""

from dataclasses import dataclass, field
from datetime import date
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

    def priority_rank(self) -> int:
        """Return a numeric rank used for sorting tasks."""
        ...


@dataclass
class ScheduledItem:
    """A CareTask placed at a specific time in a DailyPlan."""

    task: CareTask
    start_time: str
    end_time: str
    reason: str


class Owner:
    """The person managing pets and care tasks."""

    def __init__(self, name: str, available_minutes: int,
                 preferences: list[str] | None = None) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences if preferences is not None else []

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this owner."""
        ...

    def remove_task(self, task: CareTask) -> None:
        """Remove a care task from this owner."""
        ...


class Scheduler:
    """Builds a daily plan from a set of care tasks."""

    def __init__(self, available_minutes: int) -> None:
        self.available_minutes = available_minutes

    def sort_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Return tasks ordered by scheduling priority."""
        ...

    def filter_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Return the subset of tasks that fit the available time."""
        ...

    def build_plan(self, tasks: list[CareTask], start_time: str) -> "DailyPlan":
        """Assemble a DailyPlan from the given tasks."""
        ...


@dataclass
class DailyPlan:
    """The result of scheduling: placed items plus skipped tasks."""

    plan_date: date
    items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[CareTask] = field(default_factory=list)

    def total_minutes(self) -> int:
        """Return the total scheduled minutes across all items."""
        ...

    def explain(self) -> str:
        """Return a human-readable explanation of the plan."""
        ...
