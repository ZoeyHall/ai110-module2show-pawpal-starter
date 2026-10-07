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

Run the app with `streamlit run app.py`, or the terminal demo with `python main.py`.

### Main UI features

| Section | What you can do |
|---------|-----------------|
| **Owner** | Set the owner's name and how many minutes they have available today. |
| **Add a Pet** | Add a pet with a name, species (dog, cat, other) and age. Blank and duplicate names are rejected. |
| **Schedule a Task** | Add a task for a pet with a description, duration, priority (low, medium, high), optional time (`HH:MM`) and frequency (daily, weekly, once). Times like `7:30` are accepted and saved as `07:30`; invalid times like `7am` show an error. |
| **Your Tasks** | See tasks in time order, filtered by pet and by status (To do, Done, All). Pick a pending task and click **Complete** to check it off. |
| **Build Schedule** | Click **Generate schedule** to see today's plan, minutes used, any time conflicts, any skipped tasks, and a "Why this plan?" explanation. |

### Example workflow

1. **Set up the owner.** Enter "Jordan" and 60 available minutes.
2. **Add a pet.** Add Biscuit, a 4-year-old dog.
3. **Schedule tasks.** Add "Morning walk" (30 min, high, `8:00`, daily), then "Breakfast" (10 min, high, `08:15`, daily). As soon as Breakfast is added, a warning appears because it overlaps the walk (08:00–08:30).
4. **Review the task list.** "Your Tasks" lists both tasks in time order. Switch "Show pet" or "Show status" to narrow the list.
5. **Generate the schedule.** Click **Generate schedule**. The plan lists both tasks, shows "40 of 60 minutes used" and repeats the overlap as a conflict warning.
6. **Complete a task.** Choose "Morning walk" and click **Complete**. The app confirms the next daily walk was added for tomorrow. Set "Show status" to All to see today's walk marked done and tomorrow's copy as to do.
7. **Regenerate.** Today's plan now contains only Breakfast; tomorrow's walk stays out until its due date.

### Scheduler behaviors shown

- **Sorting:** tasks are listed by clock time with `Scheduler.sort_by_time()`, and untimed tasks go last. When time is short, `generate_plan()` keeps higher-priority tasks first.
- **Filtering:** the "Show pet" and "Show status" dropdowns call `Scheduler.filter_tasks()`.
- **Conflict warnings:** `Scheduler.detect_conflicts()` flags overlapping tasks, for the same pet or different pets, both when a task is added and on the generated plan. It shows warnings; it never blocks or crashes.
- **Recurring tasks:** **Complete** calls `Scheduler.mark_task_complete()`, which adds the next daily (+1 day) or weekly (+7 days) occurrence. One-time tasks don't repeat.
- **Time budget:** tasks that don't fit in the available minutes are listed as skipped.

### Sample CLI output

`python main.py` adds tasks for Biscuit and Mochi out of order (including two deliberate conflicts), then prints them sorted, filtered, completed and scheduled. Excerpt from a run on 10/07, with some sections trimmed:

```
=======================================================
All tasks, sorted by time
=======================================================
  10/07 7:30     Morning walk         Biscuit   30 min  [high] daily  todo
  10/07 07:30    Breakfast            Mochi     10 min  [high] daily  todo
  10/07 08:00    Breakfast            Biscuit   10 min  [high] daily  todo
  10/07 09:00    Give medication      Mochi      5 min  [high] once   todo
  10/07 17:00    Fetch in the yard    Biscuit   20 min  [low] daily  todo
  10/07 17:10    Nail trim            Biscuit   15 min  [medium] daily  todo
  10/07 19:00    Brush fur            Mochi     15 min  [medium] daily  todo
  10/07 20:00    Laser pointer play   Mochi     25 min  [low] daily  todo
  10/07 Anytime  Bath                 Biscuit   20 min  [medium] weekly todo
  10/07 Anytime  Clean litter box     Mochi     10 min  [medium] daily  todo

=======================================================
Completing tasks
=======================================================
  Breakfast (daily) -> next due 2026-10-08
  Bath (weekly) -> next due 2026-10-14
  Give medication (once) -> does not repeat

=======================================================
Biscuit's tasks after completing, sorted by time
=======================================================
  10/07 7:30     Morning walk         Biscuit   30 min  [high] daily  todo
  10/07 08:00    Breakfast            Biscuit   10 min  [high] daily  done
  10/08 08:00    Breakfast            Biscuit   10 min  [high] daily  todo
  10/07 17:00    Fetch in the yard    Biscuit   20 min  [low] daily  todo
  10/07 17:10    Nail trim            Biscuit   15 min  [medium] daily  todo
  10/07 Anytime  Bath                 Biscuit   20 min  [medium] weekly done
  10/14 Anytime  Bath                 Biscuit   20 min  [medium] weekly todo

=======================================================
Today's Schedule for Jordan (pending, due today)
=======================================================
  10/07 07:30    Breakfast            Mochi     10 min  [high] daily  todo
  10/07 7:30     Morning walk         Biscuit   30 min  [high] daily  todo
  10/07 17:00    Fetch in the yard    Biscuit   20 min  [low] daily  todo
  10/07 17:10    Nail trim            Biscuit   15 min  [medium] daily  todo
  10/07 19:00    Brush fur            Mochi     15 min  [medium] daily  todo
  10/07 Anytime  Clean litter box     Mochi     10 min  [medium] daily  todo

  Total: 100 of 120 minutes

  Skipped (not enough time):
  - Laser pointer play for Mochi (25 min)

=======================================================
Conflict check
=======================================================
  Warning: 'Breakfast' (07:30-07:40) overlaps 'Morning walk' (07:30-08:00) for Mochi and Biscuit.
  Warning: 'Fetch in the yard' (17:00-17:20) overlaps 'Nail trim' (17:10-17:25) for Biscuit.
```

## Testing PawPal+

Command used: python -m pytest
Sorting: tasks come back in time order, including unpadded times like "7:30", midnight and end of day. Tasks with no time or an invalid time go last. Tasks at the same time stay in priority order, and equal priorities go shortest first.
Filtering: by pet, by completed or pending status, both together, or no filter (all tasks).
Recurring tasks: daily tasks repeat the next day and weekly tasks 7 days later, across month, year and leap-day boundaries; "once" tasks don't repeat. Completing a task twice doesn't create a duplicate, overdue tasks come back overdue, and future copies stay out of today's plan.
Conflict detection: warnings for tasks at the same time or with overlapping slots, for the same pet or different pets. Back-to-back and untimed tasks don't trigger one. Bad times produce a warning instead of a crash.
Plan generation: the time budget is respected (a task that exactly fills the remaining time is scheduled; 0 minutes skips everything). Owners with no pets or no tasks get an empty plan, and completed tasks are left out.
Validation: priority is lowercased, invalid frequencies and durations of 0 or less are rejected, and remove_task() keeps completed history.


============================================================= 47 passed in 0.02s ==============================================================

Confidence Level: 4.75/5