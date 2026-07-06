# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
What classes did you include, and what responsibilities did you assign to each?
Priority (enum) : LOW / MEDIUM / HIGH. Using an enum instead of raw strings makes sorting reliable and prevents typos like "hihg".
Owner : basic info, total available_minutes for the day, and a list of preferences (the constraint inputs from the README). Owns the tasks.
Pet : name, species, breed, age. Pure data; matches the owner/pet info inputs already in app.py
CareTask : the core unit: title, duration_minutes, priority (the README's minimum requirements), plus category and recurring for the "Smarter Scheduling" table. priority_rank() converts the enum to a number for sorting.
Scheduler : the brain. Three methods map directly to the README's scheduling table: sort_tasks (by priority/duration), filter_tasks (skip tasks when time runs out), and build_plan (assemble the ordered result).
ScheduledItem : a task placed at a start_time/end_time, with a reason field so you can explain why it was scheduled there.
DailyPlan : the output: the ordered items, any skipped tasks, and explain() to satisfy the "explain the reasoning" requirement.

**b. Design changes**

- Did your design change during implementation?
My design did change, the initial uml model had recurrence as a recurring boolean. But I need replace it with the recurrence enum (none, dialy, weekly). I also put this change into the UI so that way the user can click on this, and determine how often they want the task to be repeated and completed. This is important for things like daily feedings or walks. 

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

Time budget : the owner's available_minutes is a hard cap. Nothing gets scheduled beyond it; leftover work is recorded as skipped.
Priority : every task has a LOW/MEDIUM/HIGH priority that dominates its scheduling value (priority_rank() * 10 in _value).
Preferences: categories the owner cares about get a smaller value bonus (+5), so a preferred task wins ties against an equal-priority one.

- How did you decide which constraints mattered most?
I think the time constraint was the one that mattered the most, so that way you won't be stretched so thin, and you won't be scheduled for something in the late hours or in the early early morning. 
**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
The biggest tradeoff is optimizing total value over honoring individual priority order. After reserving must-schedule tasks, the scheduler fills the remaining time with a 0/1 knapsack (_knapsack) that maximizes total value rather than greedily taking the highest-priority tasks first. So then it will sometimes drop one long high-priority task in favor of two shorter lower-priority ones when that combination produces more overall value within the same minutes. So a strict "always do the most important thing first" ordering is sacrificed for getting the most useful work done across the whole day.


- Why is that tradeoff reasonable for this scenario?
 Two 15-minute needs (a feed plus a short play) usually serve the pets better than one 45-minute task that eats the same budget, and the constraints that truly can't be compromised (recurring feeding/meds, and every pet getting attention) are already reserved before the knapsack runs, so the optimization only ever trades among the genuinely optional work. 
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used ClaudeAI for the designing, brainstorming and debugging and refactoring.
- What kinds of prompts or questions were most helpful?
Asking it to evaluate the logic and see what can be changed for better code optimization was a helpful prompt. It gave me the option to look at two different codes and see which one I thought was better, I ended up choosing the one with better readability, just for myself so that way I still felt like I could understand the code. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
For recurrence it is tested through completing the daily "feed breakfast" task and confirming the scheduler autocreated tomorrow's accurence with due date advanced by one day and completed reset to False.
For sorting: It was testing through adding the tasks deliberately out of chronological order, then verified sort_by_time reordered them earliest-first (07:30 → 18:00), with un-anchored tasks falling to the end.
Filtering was tested through checking that filter_by correctly split tasks by completion status and by pet name (case-insensitive).
Conflict detection was tested through deliberately putting two of Rex's tasks at 08:00 and confirmed the scheduler printed a warning about the overlap instead of crashing, and that the rest of the program continued normally.
- Why were these tests important?
The recurrence test is important for essential tasks (feeding, meds) so that they won't be missed. If daily feeding was missed, that would be a bad thing for the dog or pet.
The sorting and filtering tests confirm the plan is actually ordered and queryable, which is what makes the output usable rather than just a dump of tasks.
The time-budget test is the most important one, since the whole point of the scheduler is respecting the owner's limited time without overbooking them, I wanted to be sure it never scheduled past the cap and explained what it dropped.
The conflict-detection test matters because real days have double-bookings; I wanted the program to warn the user rather than fail, so a scheduling clash degrades gracefully instead of breaking the tool.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?
I am 4/5 percent confident because all of the tests were passed. I would test the edge case of empty inputs, it should print out a "Nothing scheduled due to empty fields." I would also schedule the a long, high-priority task to compete against two short lower priority ones to see if the schedule really does pick the higher-total-value combination. 
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I think I am satisified with the scheduling part of the 
**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would redesign how conflicts and scheduling interact. Right now, is only warns about overlapping tasks and moves them to other free slots. But in a different iteration, i'd make it so that way instead of moving it to another free slot, letting the owner decide. 

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
I learned how important it is to have a good design first. It is good to figure out what can be flexible versus what can't be compromised. This helped me to build out my system very well, and make the task feel more approachable. 