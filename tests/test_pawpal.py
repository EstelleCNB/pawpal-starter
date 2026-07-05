"""Unit tests for the PawPal+ pet care planner."""

from datetime import date, time, timedelta

import pytest

from pawpal_system import (
    CareTask,
    DailyPlan,
    Owner,
    Pet,
    Priority,
    Recurrence,
    Scheduler,
)


# --------------------------------------------------------------------------- #
# Small helpers so each test reads clearly.
# --------------------------------------------------------------------------- #
def make_task(
    title="Task",
    duration_minutes=30,
    priority=Priority.MEDIUM,
    category="general",
    recurrence=Recurrence.NONE,
    preferred_time=None,
    due_date=None,
):
    return CareTask(
        title=title,
        duration_minutes=duration_minutes,
        priority=priority,
        category=category,
        recurrence=recurrence,
        preferred_time=preferred_time,
        due_date=due_date,
    )


def make_scheduler(available_minutes=240, preferences=None, gap=None):
    owner = Owner(
        name="Caitlyn",
        available_minutes=available_minutes,
        preferences=preferences,
    )
    return Scheduler(owner, same_category_gap_minutes=gap), owner


# --------------------------------------------------------------------------- #
# CareTask
# --------------------------------------------------------------------------- #
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


def test_priority_rank_maps_enum_to_number():
    assert make_task(priority=Priority.HIGH).priority_rank() == 3
    assert make_task(priority=Priority.MEDIUM).priority_rank() == 2
    assert make_task(priority=Priority.LOW).priority_rank() == 1


def test_recurring_property_reflects_recurrence():
    assert make_task(recurrence=Recurrence.NONE).recurring is False
    assert make_task(recurrence=Recurrence.DAILY).recurring is True
    assert make_task(recurrence=Recurrence.WEEKLY).recurring is True


# --------------------------------------------------------------------------- #
# Recurrence.step
# --------------------------------------------------------------------------- #
def test_recurrence_step_returns_timedelta():
    assert Recurrence.DAILY.step == timedelta(days=1)
    assert Recurrence.WEEKLY.step == timedelta(days=7)


def test_recurrence_none_step_raises():
    with pytest.raises(ValueError):
        _ = Recurrence.NONE.step


# --------------------------------------------------------------------------- #
# Owner
# --------------------------------------------------------------------------- #
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


def test_add_pet_is_deduplicated():
    owner = Owner(name="Caitlyn", available_minutes=120)
    rex = Pet(name="Rex", species="dog", breed="Labrador", age=4)

    owner.add_pet(rex)
    owner.add_pet(rex)

    assert owner.pets == [rex]


def test_add_task_with_pet_registers_pet_and_links_task():
    owner = Owner(name="Caitlyn", available_minutes=120)
    rex = Pet(name="Rex", species="dog", breed="Labrador", age=4)
    task = make_task()

    owner.add_task(task, pet=rex)

    assert rex in owner.pets  # auto-registered
    assert task.pet is rex  # linked to the pet


def test_remove_task_is_a_noop_when_absent():
    owner = Owner(name="Caitlyn", available_minutes=120)
    present = make_task(title="Present")
    absent = make_task(title="Absent")
    owner.add_task(present)

    owner.remove_task(absent)  # should not raise
    assert present in owner.tasks

    owner.remove_task(present)
    assert present not in owner.tasks


def test_all_tasks_excludes_completed_by_default():
    owner = Owner(name="Caitlyn", available_minutes=120)
    done = make_task(title="Done")
    done.mark_done()
    pending = make_task(title="Pending")
    owner.add_task(done)
    owner.add_task(pending)

    assert owner.all_tasks() == [pending]
    all_including = owner.all_tasks(include_completed=True)
    assert done in all_including and pending in all_including


def test_tasks_for_filters_by_pet_identity():
    owner = Owner(name="Caitlyn", available_minutes=120)
    rex = Pet(name="Rex", species="dog", breed="Lab", age=4)
    mia = Pet(name="Mia", species="cat", breed="Tabby", age=2)
    rex_task = make_task(title="Walk Rex")
    mia_task = make_task(title="Feed Mia")
    owner.add_task(rex_task, pet=rex)
    owner.add_task(mia_task, pet=mia)

    assert owner.tasks_for(rex) == [rex_task]
    assert owner.tasks_for(mia) == [mia_task]


# --------------------------------------------------------------------------- #
# Scheduler: sorting
# --------------------------------------------------------------------------- #
def test_sort_tasks_orders_by_priority_then_preference_then_shorter():
    scheduler, _ = make_scheduler(preferences=["feeding"])
    low = make_task(title="low", priority=Priority.LOW)
    high_long = make_task(title="high_long", priority=Priority.HIGH, duration_minutes=60)
    high_short = make_task(title="high_short", priority=Priority.HIGH, duration_minutes=15)
    high_pref = make_task(
        title="high_pref", priority=Priority.HIGH, category="feeding", duration_minutes=45
    )
    tasks = [low, high_long, high_short, high_pref]

    ordered = scheduler.sort_tasks(tasks)

    # HIGH first; among HIGH the preferred one wins; then shorter beats longer.
    assert ordered == [high_pref, high_short, high_long, low]
    # original list untouched
    assert tasks == [low, high_long, high_short, high_pref]


def test_sort_by_time_puts_anchored_first_floating_last():
    scheduler, _ = make_scheduler()
    late = make_task(title="late", preferred_time=time(17, 0))
    early = make_task(title="early", preferred_time=time(6, 0))
    floating = make_task(title="floating", preferred_time=None)

    ordered = scheduler.sort_by_time([late, floating, early])

    assert ordered == [early, late, floating]


# --------------------------------------------------------------------------- #
# Scheduler: filter_by
# --------------------------------------------------------------------------- #
def test_filter_by_completed():
    scheduler, _ = make_scheduler()
    done = make_task(title="done")
    done.mark_done()
    pending = make_task(title="pending")
    tasks = [done, pending]

    assert scheduler.filter_by(tasks, completed=True) == [done]
    assert scheduler.filter_by(tasks, completed=False) == [pending]


def test_filter_by_pet_name_is_case_insensitive():
    scheduler, owner = make_scheduler()
    rex = Pet(name="Rex", species="dog", breed="Lab", age=4)
    rex_task = make_task(title="Walk Rex")
    other = make_task(title="Chores")
    owner.add_task(rex_task, pet=rex)

    result = scheduler.filter_by([rex_task, other], pet_name="rEx")

    assert result == [rex_task]


def test_filter_by_combines_criteria():
    scheduler, owner = make_scheduler()
    rex = Pet(name="Rex", species="dog", breed="Lab", age=4)
    rex_done = make_task(title="Rex done")
    rex_done.mark_done()
    rex_pending = make_task(title="Rex pending")
    owner.add_task(rex_done, pet=rex)
    owner.add_task(rex_pending, pet=rex)

    result = scheduler.filter_by(
        [rex_done, rex_pending], completed=False, pet_name="rex"
    )
    assert result == [rex_pending]


# --------------------------------------------------------------------------- #
# Scheduler: selection (filter_tasks / partition / knapsack)
# --------------------------------------------------------------------------- #
def test_filter_tasks_never_drops_recurring_essential():
    scheduler, _ = make_scheduler(available_minutes=30)
    recurring = make_task(
        title="Feed", duration_minutes=30, priority=Priority.LOW,
        recurrence=Recurrence.DAILY,
    )
    tempting = make_task(
        title="Long play", duration_minutes=30, priority=Priority.HIGH
    )

    chosen = scheduler.filter_tasks([recurring, tempting])

    # Budget only fits one; the recurring essential must survive.
    assert recurring in chosen
    assert tempting not in chosen


def test_filter_tasks_keeps_each_pets_best_for_fairness():
    scheduler, owner = make_scheduler(available_minutes=60)
    rex = Pet(name="Rex", species="dog", breed="Lab", age=4)
    mia = Pet(name="Mia", species="cat", breed="Tabby", age=2)
    rex1 = make_task(title="Rex 1", priority=Priority.HIGH, duration_minutes=30)
    rex2 = make_task(title="Rex 2", priority=Priority.HIGH, duration_minutes=30)
    mia1 = make_task(title="Mia 1", priority=Priority.MEDIUM, duration_minutes=30)
    for t, p in [(rex1, rex), (rex2, rex), (mia1, mia)]:
        owner.add_task(t, pet=p)

    chosen = scheduler.filter_tasks([rex1, rex2, mia1])

    # Without fairness, both of Rex's tasks would out-value Mia's; fairness
    # reserves Mia's top task so she isn't starved.
    assert mia1 in chosen


def test_knapsack_prefers_two_short_over_one_long():
    scheduler, _ = make_scheduler(available_minutes=60)
    long_task = make_task(title="long", priority=Priority.HIGH, duration_minutes=60)
    short1 = make_task(title="short1", priority=Priority.MEDIUM, duration_minutes=30)
    short2 = make_task(title="short2", priority=Priority.MEDIUM, duration_minutes=30)

    chosen = scheduler.filter_tasks([long_task, short1, short2])

    # Two MEDIUM shorts (value 20+20) beat one HIGH long (value 30).
    assert short1 in chosen and short2 in chosen
    assert long_task not in chosen


# --------------------------------------------------------------------------- #
# Scheduler: conflicts
# --------------------------------------------------------------------------- #
def test_detect_conflicts_flags_overlap():
    scheduler, _ = make_scheduler()
    first = make_task(title="Walk", preferred_time=time(8, 0), duration_minutes=60)
    second = make_task(title="Vet", preferred_time=time(8, 30), duration_minutes=30)

    warnings = scheduler.detect_conflicts([first, second])

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Vet" in warnings[0]


def test_detect_conflicts_ignores_non_overlapping_and_floating():
    scheduler, _ = make_scheduler()
    first = make_task(title="Walk", preferred_time=time(8, 0), duration_minutes=30)
    later = make_task(title="Vet", preferred_time=time(9, 0), duration_minutes=30)
    floating = make_task(title="Groom", preferred_time=None, duration_minutes=60)

    assert scheduler.detect_conflicts([first, later, floating]) == []


def test_detect_conflicts_names_both_pets():
    scheduler, owner = make_scheduler()
    rex = Pet(name="Rex", species="dog", breed="Lab", age=4)
    mia = Pet(name="Mia", species="cat", breed="Tabby", age=2)
    rex_task = make_task(title="Walk", preferred_time=time(8, 0), duration_minutes=60)
    mia_task = make_task(title="Feed", preferred_time=time(8, 30), duration_minutes=30)
    owner.add_task(rex_task, pet=rex)
    owner.add_task(mia_task, pet=mia)

    warning = scheduler.detect_conflicts([rex_task, mia_task])[0]

    assert "Rex" in warning and "Mia" in warning


# --------------------------------------------------------------------------- #
# Scheduler: complete_task / recurrence roll-over
# --------------------------------------------------------------------------- #
def test_complete_one_off_task_returns_none():
    scheduler, owner = make_scheduler()
    task = make_task(title="One off", recurrence=Recurrence.NONE)
    owner.add_task(task)

    result = scheduler.complete_task(task)

    assert result is None
    assert task.completed is True


def test_complete_recurring_task_schedules_next_occurrence():
    scheduler, owner = make_scheduler()
    rex = Pet(name="Rex", species="dog", breed="Lab", age=4)
    task = make_task(
        title="Feed",
        recurrence=Recurrence.DAILY,
        due_date=date(2026, 7, 5),
    )
    owner.add_task(task, pet=rex)

    follow_up = scheduler.complete_task(task)

    assert task.completed is True
    assert follow_up is not None
    assert follow_up.completed is False
    assert follow_up.due_date == date(2026, 7, 6)  # advanced by one day
    assert follow_up.pet is rex
    assert follow_up in owner.tasks  # registered on the owner


def test_complete_recurring_undated_task_stays_undated():
    scheduler, owner = make_scheduler()
    task = make_task(title="Feed", recurrence=Recurrence.WEEKLY, due_date=None)
    owner.add_task(task)

    follow_up = scheduler.complete_task(task)

    assert follow_up is not None
    assert follow_up.due_date is None


# --------------------------------------------------------------------------- #
# build_plan / DailyPlan (integration)
# --------------------------------------------------------------------------- #
def test_build_plan_places_anchored_task_at_preferred_time():
    scheduler, _ = make_scheduler(available_minutes=240)
    anchored = make_task(
        title="Breakfast", preferred_time=time(8, 0), duration_minutes=30
    )

    plan = scheduler.build_plan([anchored], start_time=time(6, 0), plan_date=date(2026, 7, 5))

    assert len(plan.items) == 1
    assert plan.items[0].start_time == time(8, 0)


def test_build_plan_spaces_same_category_tasks():
    scheduler, _ = make_scheduler(available_minutes=240, gap=30)
    walk1 = make_task(title="Walk 1", category="exercise", duration_minutes=30)
    walk2 = make_task(title="Walk 2", category="exercise", duration_minutes=30)

    plan = scheduler.build_plan(
        [walk1, walk2], start_time=time(8, 0), plan_date=date(2026, 7, 5)
    )

    starts = sorted(item.start_time for item in plan.items)
    assert len(starts) == 2
    # First 08:00-08:30, then a 30-min gap => second no earlier than 09:00.
    assert starts[0] == time(8, 0)
    assert starts[1] >= time(9, 0)


def test_build_plan_records_skipped_and_unused_minutes():
    scheduler, _ = make_scheduler(available_minutes=30)
    fits = make_task(title="Fits", priority=Priority.HIGH, duration_minutes=30)
    too_big = make_task(title="Too big", priority=Priority.LOW, duration_minutes=60)

    plan = scheduler.build_plan(
        [fits, too_big], start_time=time(8, 0), plan_date=date(2026, 7, 5)
    )

    scheduled_titles = {item.task.title for item in plan.items}
    assert "Fits" in scheduled_titles
    assert too_big in plan.skipped
    assert plan.unused_minutes == 0


def test_total_minutes_sums_scheduled_durations():
    scheduler, _ = make_scheduler(available_minutes=240)
    t1 = make_task(title="A", duration_minutes=30)
    t2 = make_task(title="B", duration_minutes=45)

    plan = scheduler.build_plan([t1, t2], start_time=time(8, 0), plan_date=date(2026, 7, 5))

    assert plan.total_minutes() == 75


def test_build_plan_with_no_tasks_is_empty():
    scheduler, _ = make_scheduler(available_minutes=120)

    plan = scheduler.build_plan([], start_time=time(8, 0), plan_date=date(2026, 7, 5))

    assert plan.items == []
    assert plan.skipped == []
    assert plan.unused_minutes == 120


def test_explain_mentions_skipped_tasks():
    scheduler, _ = make_scheduler(available_minutes=30)
    fits = make_task(title="Fits", priority=Priority.HIGH, duration_minutes=30)
    too_big = make_task(title="Big walk", priority=Priority.LOW, duration_minutes=90)

    plan = scheduler.build_plan(
        [fits, too_big], start_time=time(8, 0), plan_date=date(2026, 7, 5)
    )
    text = plan.explain()

    assert "Skipped" in text
    assert "Big walk" in text
    assert "more min" in text  # includes the deficit hint


def test_daily_plan_explain_handles_empty_plan():
    plan = DailyPlan(plan_date=date(2026, 7, 5))
    text = plan.explain()

    assert "Nothing scheduled." in text
