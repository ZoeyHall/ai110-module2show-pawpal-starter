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

==================================================
Today's Schedule for Jordan
==================================================
07:30    Morning walk         Biscuit   30 min  [high]
08:00    Breakfast            Biscuit   10 min  [high]
09:00    Give medication      Mochi      5 min  [high]
17:00    Fetch in the yard    Biscuit   20 min  [low]
19:00    Brush fur            Mochi     15 min  [medium]
Anytime  Clean litter box     Mochi     10 min  [medium]
--------------------------------------------------
Total: 90 of 90 minutes

Skipped (not enough time):
  - Laser pointer play for Mochi (25 min)

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

## 📐 Smarter Scheduling

All scheduling logic lives in `pawpal_system.py`. `Scheduler.generate_plan()` ties the features together: it takes pending tasks due today, picks the ones that fit in the owner's available time by priority, puts them in time order, and checks the result for conflicts.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()`, `time_to_minutes()` | By clock time for the plan; by priority, then shortest first, when choosing what fits |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.get_pending_tasks()` | By pet and/or completion status; plan only includes incomplete tasks due today or earlier |
| Conflict handling | `Scheduler.detect_conflicts()` | Flags overlapping time slots for the same pet or different pets; returns warnings, never crashes |
| Recurring tasks | `Task.mark_complete()`, `Scheduler.mark_task_complete()` | Daily tasks repeat +1 day, weekly +7 days, "once" tasks don't repeat |

### Sorting

- **`Scheduler.sort_by_time(tasks)`** returns tasks in order of start time.
  - Times are converted to minutes after midnight with `time_to_minutes()` before comparing, so `"7:30"` and `"07:30"` both sort before `"10:00"`. A plain string sort would put `"7:30"` after `"10:00"`.
  - Tasks with no time, or a time that can't be read, go last.
  - The sort is stable, so tasks at the same time keep their priority order.
- **`Scheduler.sort_tasks(tasks)`** sorts by priority (high → low), then by shortest duration. `generate_plan()` uses this order to decide which tasks fit; putting shorter tasks first among equal priorities fits more tasks into the day.

### Filtering

- **`Scheduler.filter_tasks(pet_name=None, completed=None)`** returns tasks for one pet, by completion status, or both. Leaving a filter as `None` means "don't filter on this":
  - `filter_tasks(pet_name="Mochi")`: all of Mochi's tasks
  - `filter_tasks(completed=False)`: pending tasks for every pet
  - `filter_tasks("Biscuit", True)`: Biscuit's completed tasks
- **`Scheduler.get_pending_tasks(on_date=None)`** returns incomplete tasks due on or before a date (today by default). Overdue tasks stay in the plan; future copies of recurring tasks are left out until their day.

### Conflict detection

- **`Scheduler.detect_conflicts(tasks)`** returns a list of warning messages for tasks whose time slots overlap, for example:

  ```
  Warning: 'Fetch in the yard' (17:00-17:20) overlaps 'Nail trim' (17:10-17:25) for Biscuit.
  ```

- Each task takes up the slot from its start time to start + duration. Back-to-back tasks (one ends at 08:00, the next starts at 08:00) are not a conflict.
- It works for two tasks for the same pet and for tasks for different pets.
- **How it works:** sort tasks by start time, then compare each task with the ones after it, stopping as soon as a later task starts after the current one ends.
- **Lightweight by design:** it never raises an error. Tasks with no time are ignored, and a task with an unreadable time (such as `"7am"` or `"25:00"`) gets its own warning.
- `generate_plan()` runs it on the final plan and stores the warnings in `Scheduler.conflicts`. `explain_plan()` includes them in its text.

### Recurring tasks

- Each `Task` has a `frequency` (`"daily"`, `"weekly"` or `"once"`) and a `due_date` (today by default).
- **`Task.mark_complete()`** marks the task done and returns a copy for its next occurrence, with the due date moved forward: +1 day for daily, +7 days for weekly. A `"once"` task returns `None`.
- **`Scheduler.mark_task_complete(task)`** does the same and also adds the new copy to the task's pet, so the next occurrence isn't lost. `main.py` uses it to complete a daily, a weekly and a one-time task.
- The next due date counts from the old due date, not from the day the task was done. A task finished late comes back already overdue, so a missed day isn't silently skipped.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
