# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
Priority (enum) — LOW / MEDIUM / HIGH. Using an enum instead of raw strings makes sorting reliable and prevents typos like "hihg".
Owner — basic info, total available_minutes for the day, and a list of preferences (the constraint inputs from the README). Owns the tasks.
Pet — name, species, breed, age. Pure data; matches the owner/pet info inputs already in app.py:42-44.
CareTask — the core unit: title, duration_minutes, priority (the README's minimum requirements), plus category and recurring for the "Smarter Scheduling" table. priority_rank() converts the enum to a number for sorting.
Scheduler — the brain. Three methods map directly to the README's scheduling table: sort_tasks (by priority/duration), filter_tasks (skip tasks when time runs out), and build_plan (assemble the ordered result).
ScheduledItem — a task placed at a start_time/end_time, with a reason field so you can explain why it was scheduled there.
DailyPlan — the output: the ordered items, any skipped tasks, and explain() to satisfy the "explain the reasoning" requirement.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
