# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

Plan for 2026-07-05 (100 min scheduled, 20 min free):
  08:00-08:20  Morning walk (for Mochi) — HIGH priority; matches a preference
  08:20-09:20  potty training (for Mochi) — HIGH priority
  09:20-09:40  Breakfast (for Dash) — MEDIUM priority; matches a preference
Skipped (couldn't fit):
  - Getting a bath (60 min) — need 40 more min; consider shortening or dropping “Breakfast” (20 min)

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

(.venv) caitlynbennett@Estelles-MacBook-Pro pawpal-starter % python -m pytest
======================================================================================== test session starts =========================================================================================
platform darwin -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/caitlynbennett/ai_engineering1101/module3/pawpal-starter
plugins: anyio-4.14.0
collected 2 items                                                                                                                                                                                    

tests/test_pawpal.py ..                                                                                                                                                                                                                                                                                                                                      [100%]
========================================================================================= 2 passed in 0.02s ==========================================================================================


## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. Launch the app
2. Under "Owner and Pet" enter a pet, and enter in the name, age, and breed of the pet. 
3. Add a task, give the task a title, how long it will take, and also the priority.
4.Build a schedule by clicking the build schedule button. 
5. Mark recurring tasks as done


**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->


Sample output:
Today's Schedule
========================================
Plan for 2026-07-05 (110 min scheduled):
  08:00-08:45  Morning walk (for Rex) — HIGH priority, matches a preference; 120 min were free
  08:45-09:00  Feed breakfast (for Milo) — HIGH priority; 75 min were free
  09:00-09:20  Brush coat (for Milo) — MEDIUM priority; 60 min were free
  09:20-09:50  Play fetch (for Rex) — LOW priority, matches a preference; 40 min were free


============== Smarter Scheduling section: ===========================

Sorting behavior:
Two separate sorts:
sort_tasks: orders by scheduling importance. The sort key is a tuple (priority_rank, is_preferred, duration) with reverse=True, so it ranks: highest priority first, then owner-preferred categories, then shorter tasks (so more fit). Original list is untouched.
sort_by_time: orders chronologically by preferred_time. Anchored tasks come earliest-first; floating tasks (no preferred time) sort to the end using time.max as their key.
Filtering:
filter_by: plain attribute filter. Optionally keeps tasks matching a completed status and/or a pet_name (case-insensitive via casefold()). None criteria are skipped, so you can pass either or both.
filter_task: the smart time-budget filter. It partitions tasks into must-schedule (recurring essentials + each pet's single highest-value task, for fairness) vs. optional. Must-schedule tasks are reserved first (highest value first), then the leftover minutes are filled optimally by a 0/1 knapsack that maximizes total _value (priority×10 + preference bonus) rather than greedily packing.
Conflict detection
detect_conflicts: a non-mutating, non-fatal check. It only considers anchored tasks (floating tasks can't clash), sorts them by start time, and compares each task's window (preferred_time, preferred_time + duration) against later ones. Because they're sorted, it breaks early once a later task starts at/after the current one's end. Each overlap produces a human-readable warning naming the pet(s) and times. Returns [] when clean.

Recurring task:
Driven by the Recurrence enum (NONE/DAILY/WEEKLY, whose value doubles as a day-step timedelta). When complete_task runs, it marks the task done; if it recurs, it builds a fresh uncompleted copy through(_next_occurrence — same attributes), reset completed, and due_date advanced by the recurrence step — then registers it on the owner and returns it. One-off tasks just get marked done and return None.

======= TESTING PAWPAL========
CareTask — status changes (mark_done), priority ranking, and the recurring flag
Recurrence — the .step timedelta for daily/weekly and the error for NONE
Owner — pet de-duplication, task-to-pet linking, task removal, and completed-task filtering
Scheduler sorting/filtering — ordering by priority/preference/duration, chronological sorting, and filtering by completion status and pet name
Task selection — recurring essentials always kept, per-pet fairness, and knapsack picking the best-value mix within the time budget
Conflict detection — flagging overlapping anchored tasks and naming the pets involved
Recurrence roll-over — completing tasks spawns the next occurrence with an advanced due date
Plan building — anchored placement, category spacing, skipped tasks, unused minutes, totals, and the human-readable explain() output


(.venv) caitlynbennett@Estelles-MacBook-Pro pawpal-starter % python -m pytest
========================================================================= test session starts =========================================================================
platform darwin -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/caitlynbennett/ai_engineering1101/module3/pawpal-starter
plugins: anyio-4.14.0
collected 32 items                                                                                                                                                    

tests/test_pawpal.py ................................                                                                                                           [100%]

========================================================================= 32 passed in 0.02s ====