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


class Recurrence(Enum):
    """How often a care task repeats.

    The value is the number of days between occurrences, so ``step`` can turn
    it straight into a ``timedelta`` (NONE has no step).
    """

    NONE = 0
    DAILY = 1
    WEEKLY = 7

    @property
    def step(self) -> timedelta:
        """The gap to the next occurrence (undefined for NONE)."""
        if self is Recurrence.NONE:
            raise ValueError("Recurrence.NONE has no next occurrence")
        return timedelta(days=self.value)


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
    recurrence: "Recurrence" = Recurrence.NONE
    completed: bool = False
    pet: "Pet | None" = None
    # Optional anchor: if set, the scheduler tries to place the task at this
    # time of day (e.g. feed breakfast at 08:00) instead of packing it
    # wherever it fits. Tasks without an anchor float freely in the day.
    preferred_time: "time | None" = None
    # The date this particular occurrence is for. Recurring tasks advance it
    # automatically when completed; ``None`` means undated.
    due_date: "date | None" = None

    @property
    def recurring(self) -> bool:
        """Whether this task repeats (daily or weekly)."""
        return self.recurrence is not Recurrence.NONE

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

    #: Minimum spacing between two placed tasks sharing a category, so the
    #: owner isn't asked to do (say) two walks back-to-back.
    DEFAULT_CATEGORY_GAP_MINUTES = 30

    def __init__(self, owner: Owner,
                 same_category_gap_minutes: int | None = None) -> None:
        """Create a scheduler bound to the given owner."""
        self.owner = owner
        self.same_category_gap_minutes = (
            self.DEFAULT_CATEGORY_GAP_MINUTES
            if same_category_gap_minutes is None
            else same_category_gap_minutes
        )

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

    def _value(self, task: CareTask) -> int:
        """Return the scheduling value of a task (higher = more worth fitting).

        Priority dominates; a preferred category adds a smaller bonus. This
        is the objective the knapsack selection maximizes.
        """
        value = task.priority_rank() * 10
        if self._preferred(task):
            value += 5
        return value

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

    def sort_by_time(self, tasks: list[CareTask]) -> list[CareTask]:
        """Return tasks ordered chronologically by their anchored time.

        Tasks with a ``preferred_time`` are ordered earliest-first; tasks
        without one (which float freely in the day) sort to the end. The
        original list is left untouched.
        """
        return sorted(
            tasks,
            key=lambda t: t.preferred_time if t.preferred_time is not None
            else time.max,
        )

    def filter_by(self, tasks: list[CareTask], *,
                  completed: bool | None = None,
                  pet_name: str | None = None) -> list[CareTask]:
        """Return the subset of tasks matching the given criteria.

        ``completed`` — if given, keep only tasks whose completion status
        matches (``False`` for outstanding work, ``True`` for finished).
        ``pet_name`` — if given, keep only tasks belonging to a pet with that
        name (case-insensitive). Criteria left as ``None`` are ignored, so
        either or both may be supplied.
        """
        result = list(tasks)
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        if pet_name is not None:
            target = pet_name.casefold()
            result = [
                t for t in result
                if t.pet is not None and t.pet.name.casefold() == target
            ]
        return result

    def _partition_tasks(
        self, tasks: list[CareTask]
    ) -> tuple[list[CareTask], list[CareTask]]:
        """Split tasks into must-schedule vs. optional.

        Must-schedule captures two commitments:
          * recurring essentials (feeding, meds) — never silently dropped;
          * per-pet fairness — every pet's single highest-value task, so no
            pet is starved of attention by another pet's long to-do list.
        Everything else is optional and competes for the leftover time.
        """
        must: list[CareTask] = []

        for task in tasks:
            if task.recurring and task not in must:
                must.append(task)

        pets: list[Pet] = []
        for task in tasks:
            if task.pet is not None and task.pet not in pets:
                pets.append(task.pet)
        for pet in pets:
            pet_tasks = [t for t in tasks if t.pet is pet]
            if pet_tasks:
                best = max(pet_tasks, key=self._value)
                if best not in must:
                    must.append(best)

        optional = [t for t in tasks if t not in must]
        return must, optional

    def _knapsack(self, tasks: list[CareTask], capacity: int) -> list[CareTask]:
        """Pick the subset of ``tasks`` maximizing total value within capacity.

        Classic 0/1 knapsack by minutes: unlike greedy packing, this will
        trade one long high-priority task for two shorter ones when that
        serves the pets better overall. Task counts are tiny, so the DP is
        instant.
        """
        if not tasks or capacity <= 0:
            return []

        n = len(tasks)
        best = [[0] * (capacity + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            weight = tasks[i - 1].duration_minutes
            value = self._value(tasks[i - 1])
            row, prev = best[i], best[i - 1]
            for c in range(capacity + 1):
                row[c] = prev[c]
                if weight <= c:
                    candidate = prev[c - weight] + value
                    if candidate > row[c]:
                        row[c] = candidate

        chosen: list[CareTask] = []
        c = capacity
        for i in range(n, 0, -1):
            if best[i][c] != best[i - 1][c]:
                chosen.append(tasks[i - 1])
                c -= tasks[i - 1].duration_minutes
        chosen.reverse()
        return chosen

    def filter_tasks(self, tasks: list[CareTask]) -> list[CareTask]:
        """Return the subset of tasks that best fills the available time.

        Must-schedule tasks (recurring essentials and each pet's top task)
        are reserved first; the remaining budget is then filled optimally by
        knapsack rather than greedily.
        """
        must, optional = self._partition_tasks(tasks)

        remaining = self.available_minutes
        chosen: list[CareTask] = []
        for task in sorted(must, key=self._value, reverse=True):
            if task.duration_minutes <= remaining:
                chosen.append(task)
                remaining -= task.duration_minutes

        chosen.extend(self._knapsack(optional, remaining))
        return chosen

    def detect_conflicts(self, tasks: list[CareTask]) -> list[str]:
        """Return warnings for anchored tasks whose time windows overlap.

        Lightweight, non-fatal check: it only looks at tasks with a
        ``preferred_time`` (floating tasks can't clash because they have no
        requested slot) and compares each anchored task's
        ``[preferred_time, preferred_time + duration)`` window against every
        other's. Any overlap — whether the tasks are for the same pet or
        different pets — yields a human-readable warning string. It never
        mutates the tasks and never raises; an empty list means no clashes.
        """
        anchored = sorted(
            (t for t in tasks if t.preferred_time is not None),
            key=lambda t: t.preferred_time,  # type: ignore[arg-type,return-value]
        )

        warnings: list[str] = []
        for i, first in enumerate(anchored):
            first_start = first.preferred_time
            first_end = (
                datetime.combine(date.min, first_start)
                + timedelta(minutes=first.duration_minutes)
            ).time()
            for second in anchored[i + 1:]:
                second_start = second.preferred_time
                # Sorted by start time, so once a later task starts at or after
                # this one's end, nothing further can overlap it.
                if second_start >= first_end:
                    break
                first_pet = first.pet.name if first.pet else "you"
                second_pet = second.pet.name if second.pet else "you"
                who = (
                    f"for {first_pet}"
                    if first_pet == second_pet
                    else f"for {first_pet} and {second_pet}"
                )
                warnings.append(
                    f"Conflict {who}: “{first.title}” "
                    f"({first_start:%H:%M}-{first_end:%H:%M}) overlaps "
                    f"“{second.title}” (starts {second_start:%H:%M})"
                )
        return warnings

    @staticmethod
    def _find_slot(earliest: datetime, duration: int,
                   occupied: list[tuple[datetime, datetime]]) -> datetime:
        """Earliest start >= ``earliest`` where ``duration`` fits without overlap.

        ``occupied`` must be sorted by start time.
        """
        cursor = earliest
        span = timedelta(minutes=duration)
        for start, end in occupied:
            if cursor + span <= start:
                return cursor
            if end > cursor:
                cursor = end
        return cursor

    def _reason(self, task: CareTask) -> str:
        """Explain, in words, why a task was scheduled the way it was."""
        parts = [f"{task.priority.name} priority"]
        if task.recurring:
            parts.append("recurring essential")
        if self._preferred(task):
            parts.append("matches a preference")
        if task.preferred_time is not None:
            parts.append(f"anchored near {task.preferred_time:%H:%M}")
        return "; ".join(parts)

    def _place(self, chosen: list[CareTask], start_time: time,
               plan_date: date) -> list[ScheduledItem]:
        """Lay chosen tasks on a timeline honoring anchors and category spacing.

        Anchored tasks claim their preferred time first (bumped later only to
        avoid an overlap); flexible tasks then fill the earliest free slot in
        value order. Two tasks of the same category are kept at least
        ``same_category_gap_minutes`` apart.
        """
        base = datetime.combine(plan_date, start_time)

        anchored = [t for t in chosen if t.preferred_time is not None]
        flexible = [t for t in chosen if t.preferred_time is None]
        anchored.sort(key=lambda t: t.preferred_time)  # type: ignore[arg-type,return-value]
        flexible.sort(key=self._value, reverse=True)

        occupied: list[tuple[datetime, datetime]] = []
        last_end_by_category: dict[str, datetime] = {}
        items: list[ScheduledItem] = []

        for task in anchored + flexible:
            if task.preferred_time is not None:
                earliest = max(base, datetime.combine(plan_date, task.preferred_time))
            else:
                earliest = base

            prev_end = last_end_by_category.get(task.category)
            if prev_end is not None:
                spaced = prev_end + timedelta(minutes=self.same_category_gap_minutes)
                if spaced > earliest:
                    earliest = spaced

            start_dt = self._find_slot(earliest, task.duration_minutes, occupied)
            end_dt = start_dt + timedelta(minutes=task.duration_minutes)

            occupied.append((start_dt, end_dt))
            occupied.sort(key=lambda interval: interval[0])
            current = last_end_by_category.get(task.category)
            if current is None or end_dt > current:
                last_end_by_category[task.category] = end_dt

            items.append(
                ScheduledItem(
                    task=task,
                    start_time=start_dt.time(),
                    end_time=end_dt.time(),
                    reason=self._reason(task),
                )
            )

        items.sort(key=lambda item: item.start_time)
        return items

    def _next_occurrence(self, task: CareTask) -> CareTask:
        """Return a fresh, uncompleted copy of ``task`` for its next cycle.

        The new occurrence keeps every scheduling attribute but resets its
        completion, and advances ``due_date`` by the recurrence step when a
        date is present (an undated task simply reappears as pending).
        """
        next_due = (
            task.due_date + task.recurrence.step
            if task.due_date is not None
            else None
        )
        return CareTask(
            title=task.title,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            category=task.category,
            recurrence=task.recurrence,
            completed=False,
            pet=task.pet,
            preferred_time=task.preferred_time,
            due_date=next_due,
        )

    def complete_task(self, task: CareTask) -> CareTask | None:
        """Mark ``task`` done and, if it recurs, schedule its next occurrence.

        For a daily or weekly task this registers a fresh uncompleted instance
        on the owner (for the same pet) and returns it. One-off tasks are just
        marked complete and ``None`` is returned.
        """
        task.mark_done()
        if not task.recurring:
            return None

        follow_up = self._next_occurrence(task)
        self.owner.add_task(follow_up, pet=follow_up.pet)
        return follow_up

    def build_plan(self, tasks: list[CareTask], start_time: time,
                   plan_date: date) -> "DailyPlan":
        """Assemble a DailyPlan from the given tasks.

        Tasks are selected to maximize value within the time budget (reserving
        recurring essentials and per-pet fairness first), then placed on a
        timeline that respects anchored times and spaces out same-category
        work. Whatever doesn't make the cut is recorded as skipped.
        """
        chosen = self.filter_tasks(tasks)
        chosen_ids = {id(t) for t in chosen}

        plan = DailyPlan(plan_date=plan_date)
        plan.items = self._place(chosen, start_time, plan_date)
        plan.skipped = [t for t in tasks if id(t) not in chosen_ids]
        used = sum(t.duration_minutes for t in chosen)
        plan.unused_minutes = max(0, self.available_minutes - used)
        return plan


@dataclass
class DailyPlan:
    """The result of scheduling: placed items plus skipped tasks."""

    plan_date: date
    items: list[ScheduledItem] = field(default_factory=list)
    skipped: list[CareTask] = field(default_factory=list)
    unused_minutes: int = 0

    def total_minutes(self) -> int:
        """Return the total scheduled minutes across all items."""
        return sum(item.task.duration_minutes for item in self.items)

    def explain(self) -> str:
        """Return a human-readable explanation of the plan."""
        lines = [
            f"Plan for {self.plan_date.isoformat()} "
            f"({self.total_minutes()} min scheduled, {self.unused_minutes} min free):"
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
            lines.append("Skipped (couldn't fit):")
            # The cheapest item to sacrifice is the lowest-priority scheduled
            # task (ties broken toward the longest, since it frees the most).
            droppable = None
            if self.items:
                droppable = min(
                    self.items,
                    key=lambda it: (it.task.priority.value, -it.task.duration_minutes),
                )
            for task in self.skipped:
                deficit = max(0, task.duration_minutes - self.unused_minutes)
                line = f"  - {task.title} ({task.duration_minutes} min)"
                if deficit > 0 and droppable is not None:
                    line += (
                        f" — need {deficit} more min; consider shortening or "
                        f"dropping “{droppable.task.title}” "
                        f"({droppable.task.duration_minutes} min)"
                    )
                elif deficit > 0:
                    line += f" — need {deficit} more min in the day"
                lines.append(line)

        return "\n".join(lines)
