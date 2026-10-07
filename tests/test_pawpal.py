"""Tests for PawPal+ core classes."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Biscuit", species="dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", 10, "high"))

    assert len(pet.tasks) == 1


def test_sort_by_time_handles_unpadded_hours():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))
    tasks = [
        Task("B", 5, time="10:00"),
        Task("A", 5, time="7:30"),
        Task("C", 5),
    ]

    result = scheduler.sort_by_time(tasks)

    assert [t.description for t in result] == ["A", "B", "C"]


def _owner_with_tasks():
    owner = Owner(name="Sam", available_minutes=60)
    dog = Pet(name="Biscuit", species="dog")
    cat = Pet(name="Mochi", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Walk", 30))
    dog.add_task(Task("Breakfast", 10))
    cat.add_task(Task("Brush fur", 15))
    dog.tasks[1].mark_complete()
    return owner


def test_filter_tasks_by_pet_name():
    scheduler = Scheduler(_owner_with_tasks())

    result = scheduler.filter_tasks(pet_name="Mochi")

    assert [t.description for t in result] == ["Brush fur"]


def test_filter_tasks_by_completion_status():
    scheduler = Scheduler(_owner_with_tasks())

    done = scheduler.filter_tasks(completed=True)
    pending = scheduler.filter_tasks(completed=False)

    assert [t.description for t in done] == ["Breakfast"]
    assert [t.description for t in pending] == ["Walk", "Brush fur"]


def test_filter_tasks_combines_filters_and_defaults_to_all():
    scheduler = Scheduler(_owner_with_tasks())

    assert [t.description for t in scheduler.filter_tasks("Biscuit", False)] == ["Walk"]
    assert len(scheduler.filter_tasks()) == 3
    assert scheduler.filter_tasks(pet_name="Nobody") == []


def test_daily_task_creates_next_day_occurrence():
    task = Task("Walk", 30, frequency="daily", due_date=date(2026, 10, 7))

    next_task = task.mark_complete()

    assert task.completed is True
    assert next_task is not None
    assert next_task.completed is False
    assert next_task.due_date == date(2026, 10, 8)
    assert next_task.description == "Walk"


def test_weekly_task_creates_occurrence_seven_days_later():
    task = Task("Bath", 20, frequency="weekly", due_date=date(2026, 10, 7))

    next_task = task.mark_complete()

    assert next_task.due_date == date(2026, 10, 14)


def test_once_task_does_not_repeat():
    task = Task("Vet visit", 60, frequency="once")

    assert task.mark_complete() is None


def test_scheduler_adds_next_occurrence_to_pet():
    owner = Owner(name="Sam", available_minutes=60)
    dog = Pet(name="Biscuit", species="dog")
    owner.add_pet(dog)
    dog.add_task(Task("Walk", 30))
    scheduler = Scheduler(owner)

    next_task = scheduler.mark_task_complete(dog.tasks[0])

    assert len(dog.tasks) == 2
    assert dog.tasks[1] is next_task
    assert next_task.pet_name == "Biscuit"


def test_future_occurrence_not_scheduled_today():
    owner = Owner(name="Sam", available_minutes=60)
    dog = Pet(name="Biscuit", species="dog")
    owner.add_pet(dog)
    dog.add_task(Task("Walk", 30))
    scheduler = Scheduler(owner)

    scheduler.mark_task_complete(dog.tasks[0])

    assert scheduler.generate_plan() == []
    tomorrow = date.today() + timedelta(days=1)
    assert len(scheduler.get_pending_tasks(on_date=tomorrow)) == 1


def test_invalid_frequency_rejected():
    with pytest.raises(ValueError):
        Task("Walk", 30, frequency="monthly")


def test_detect_conflicts_same_start_time_different_pets():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))
    walk = Task("Walk", 30, time="07:30", pet_name="Biscuit")
    feed = Task("Breakfast", 10, time="7:30", pet_name="Mochi")

    warnings = scheduler.detect_conflicts([walk, feed])

    assert len(warnings) == 1
    assert "Walk" in warnings[0] and "Breakfast" in warnings[0]
    assert "Biscuit and Mochi" in warnings[0]


def test_detect_conflicts_overlap_same_pet():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))
    fetch = Task("Fetch", 20, time="17:00", pet_name="Biscuit")
    trim = Task("Nail trim", 15, time="17:10", pet_name="Biscuit")

    warnings = scheduler.detect_conflicts([trim, fetch])

    assert len(warnings) == 1
    assert "for Biscuit." in warnings[0]


def test_back_to_back_and_untimed_tasks_do_not_conflict():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))
    tasks = [
        Task("Walk", 30, time="07:30"),
        Task("Breakfast", 10, time="08:00"),
        Task("Litter box", 10),
        Task("Brush", 10),
    ]

    assert scheduler.detect_conflicts(tasks) == []


def test_detect_conflicts_warns_on_bad_time_instead_of_crashing():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))
    tasks = [Task("Walk", 30, time="7am"), Task("Feed", 10, time="25:00")]

    warnings = scheduler.detect_conflicts(tasks)

    assert len(warnings) == 2
    assert all("unreadable time" in w for w in warnings)


def test_generate_plan_records_conflicts():
    owner = Owner(name="Sam", available_minutes=60)
    dog = Pet(name="Biscuit", species="dog")
    cat = Pet(name="Mochi", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)
    dog.add_task(Task("Walk", 20, time="08:00"))
    cat.add_task(Task("Breakfast", 10, time="08:00"))
    scheduler = Scheduler(owner)

    scheduler.generate_plan()

    assert len(scheduler.conflicts) == 1
    assert scheduler.conflicts[0] in scheduler.explain_plan()


# --- Edge cases: recurring tasks ---------------------------------------------


def _scheduler_with_one_task(task: Task, available_minutes: int = 60):
    owner = Owner(name="Sam", available_minutes=available_minutes)
    dog = Pet(name="Biscuit", species="dog")
    owner.add_pet(dog)
    dog.add_task(task)
    return Scheduler(owner), dog


@pytest.mark.parametrize(
    "frequency, due, expected",
    [
        ("daily", date(2026, 10, 31), date(2026, 11, 1)),  # month boundary
        ("weekly", date(2026, 12, 29), date(2027, 1, 5)),  # year boundary
        ("daily", date(2028, 2, 28), date(2028, 2, 29)),  # leap day
        ("daily", date(2028, 2, 29), date(2028, 3, 1)),  # after leap day
    ],
)
def test_next_occurrence_crosses_calendar_boundaries(frequency, due, expected):
    task = Task("Walk", 30, frequency=frequency, due_date=due)

    assert task.mark_complete().due_date == expected


def test_next_occurrence_copies_task_details():
    task = Task(
        "Medication", 5, "high", time="09:00", frequency="daily", pet_name="Mochi"
    )

    next_task = task.mark_complete()

    assert next_task is not task
    assert (next_task.description, next_task.duration_minutes) == ("Medication", 5)
    assert (next_task.priority, next_task.time) == ("high", "09:00")
    assert (next_task.frequency, next_task.pet_name) == ("daily", "Mochi")


def test_overdue_task_completed_late_comes_back_overdue():
    three_days_ago = date.today() - timedelta(days=3)
    scheduler, dog = _scheduler_with_one_task(
        Task("Walk", 30, frequency="daily", due_date=three_days_ago)
    )

    next_task = scheduler.mark_task_complete(dog.tasks[0])

    assert next_task.due_date == date.today() - timedelta(days=2)
    assert scheduler.generate_plan() == [next_task]


def test_once_task_does_not_add_a_new_task_to_pet():
    scheduler, dog = _scheduler_with_one_task(Task("Vet visit", 60, frequency="once"))

    scheduler.mark_task_complete(dog.tasks[0])

    assert len(dog.tasks) == 1


def test_completing_same_task_twice_adds_only_one_occurrence():
    scheduler, dog = _scheduler_with_one_task(Task("Walk", 30))

    first = scheduler.mark_task_complete(dog.tasks[0])
    second = scheduler.mark_task_complete(dog.tasks[0])

    assert first is not None
    assert second is None
    assert len(dog.tasks) == 2


def test_remove_task_after_recurrence_keeps_completed_history():
    scheduler, dog = _scheduler_with_one_task(Task("Walk", 30))
    scheduler.mark_task_complete(dog.tasks[0])

    dog.remove_task("Walk")

    assert [t.completed for t in dog.tasks] == [True]


# --- Edge cases: sorting -----------------------------------------------------


def test_same_time_keeps_priority_order_in_plan():
    owner = Owner(name="Sam", available_minutes=60)
    dog = Pet(name="Biscuit", species="dog")
    owner.add_pet(dog)
    dog.add_task(Task("Play", 10, "low", time="08:00"))
    dog.add_task(Task("Medication", 5, "high", time="08:00"))
    dog.add_task(Task("Brush", 10, "medium", time="08:00"))

    plan = Scheduler(owner).generate_plan()

    assert [t.priority for t in plan] == ["high", "medium", "low"]


def test_sort_by_time_midnight_and_end_of_day():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))
    tasks = [
        Task("Late", 5, time="23:59"),
        Task("Anytime", 5),
        Task("Midnight", 5, time="00:00"),
    ]

    result = scheduler.sort_by_time(tasks)

    assert [t.description for t in result] == ["Midnight", "Late", "Anytime"]


def test_sort_by_time_puts_invalid_times_last_without_crashing():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))
    tasks = [Task("Bad", 5, time="7am"), Task("Good", 5, time="08:00")]

    result = scheduler.sort_by_time(tasks)

    assert [t.description for t in result] == ["Good", "Bad"]


def test_sort_by_time_empty_list():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))

    assert scheduler.sort_by_time([]) == []


def test_sort_tasks_breaks_priority_ties_by_shorter_duration():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))
    tasks = [
        Task("Long", 30, "high"),
        Task("Low", 5, "low"),
        Task("Short", 10, "high"),
    ]

    result = scheduler.sort_tasks(tasks)

    assert [t.description for t in result] == ["Short", "Long", "Low"]


# --- Edge cases: plan generation and time budget ------------------------------


def test_task_exactly_filling_remaining_time_is_scheduled():
    scheduler, _ = _scheduler_with_one_task(Task("Walk", 60), available_minutes=60)

    plan = scheduler.generate_plan()

    assert len(plan) == 1
    assert scheduler.total_scheduled_minutes() == 60


def test_zero_available_minutes_skips_everything():
    scheduler, _ = _scheduler_with_one_task(Task("Walk", 5), available_minutes=0)

    assert scheduler.generate_plan() == []
    assert len(scheduler.skipped) == 1


def test_owner_with_no_pets_gets_empty_plan():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))

    assert scheduler.generate_plan() == []
    assert scheduler.explain_plan() == "No pending tasks to schedule."


def test_pet_with_no_tasks_gets_empty_plan():
    owner = Owner(name="Sam", available_minutes=60)
    owner.add_pet(Pet(name="Biscuit", species="dog"))

    assert Scheduler(owner).generate_plan() == []


def test_greedy_skips_long_high_priority_but_fits_short_low_priority():
    owner = Owner(name="Sam", available_minutes=30)
    dog = Pet(name="Biscuit", species="dog")
    owner.add_pet(dog)
    dog.add_task(Task("Walk", 20, "high"))
    dog.add_task(Task("Vet trip", 40, "high"))
    dog.add_task(Task("Treat", 5, "low"))
    scheduler = Scheduler(owner)

    plan = scheduler.generate_plan()

    assert {t.description for t in plan} == {"Walk", "Treat"}
    assert [t.description for t in scheduler.skipped] == ["Vet trip"]


def test_completed_tasks_left_out_of_plan_and_skipped():
    scheduler, dog = _scheduler_with_one_task(Task("Walk", 30, frequency="once"))
    dog.tasks[0].mark_complete()

    assert scheduler.generate_plan() == []
    assert scheduler.skipped == []


# --- Edge cases: conflict detection ------------------------------------------


def test_long_task_overlapping_two_short_tasks_reports_both():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=120))
    tasks = [
        Task("Long walk", 60, time="08:00"),
        Task("Feed", 10, time="08:10"),
        Task("Meds", 5, time="08:40"),
    ]

    warnings = scheduler.detect_conflicts(tasks)

    assert len(warnings) == 2
    assert all("Long walk" in w for w in warnings)


def test_three_tasks_at_same_time_report_every_pair():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=120))
    tasks = [Task(name, 10, time="08:00") for name in ("A", "B", "C")]

    assert len(scheduler.detect_conflicts(tasks)) == 3


def test_task_crossing_midnight_is_not_compared_with_next_day():
    # Known limitation: each day is checked on its own, so a task running past
    # midnight does not conflict with an early-morning task.
    scheduler = Scheduler(Owner(name="Sam", available_minutes=120))
    tasks = [Task("Late walk", 60, time="23:30"), Task("Early feed", 10, time="00:15")]

    assert scheduler.detect_conflicts(tasks) == []


# --- Edge cases: input validation --------------------------------------------


def test_priority_is_normalized_to_lowercase():
    assert Task("Walk", 30, priority="HIGH").priority == "high"


@pytest.mark.parametrize("duration", [0, -5])
def test_non_positive_duration_rejected(duration):
    with pytest.raises(ValueError):
        Task("Walk", duration)


def test_remove_task_removes_pending_only():
    dog = Pet(name="Biscuit", species="dog")
    dog.add_task(Task("Walk", 30))
    dog.add_task(Task("Walk", 30))
    dog.add_task(Task("Feed", 10))
    dog.tasks[0].mark_complete()

    dog.remove_task("Walk")

    assert [(t.description, t.completed) for t in dog.tasks] == [
        ("Walk", True),
        ("Feed", False),
    ]


# --- Core requirements --------------------------------------------------------


def test_sorting_correctness_returns_chronological_order():
    scheduler = Scheduler(Owner(name="Sam", available_minutes=60))
    times = ["17:00", "08:00", "7:30", "20:00", "09:00", "00:05", "12:45"]
    tasks = [Task(f"Task at {t}", 5, time=t) for t in times]

    result = scheduler.sort_by_time(tasks)

    assert [t.time for t in result] == [
        "00:05", "7:30", "08:00", "09:00", "12:45", "17:00", "20:00"
    ]


def test_recurrence_daily_task_complete_creates_task_for_following_day():
    today = date(2026, 10, 7)
    scheduler, dog = _scheduler_with_one_task(
        Task("Morning walk", 30, "high", time="07:30", frequency="daily", due_date=today)
    )
    original = dog.tasks[0]

    new_task = scheduler.mark_task_complete(original)

    assert original.completed is True
    assert new_task in dog.tasks
    assert new_task.description == "Morning walk"
    assert new_task.due_date == today + timedelta(days=1)
    assert new_task.completed is False


def test_conflict_detection_flags_duplicate_times():
    owner = Owner(name="Sam", available_minutes=60)
    dog = Pet(name="Biscuit", species="dog")
    owner.add_pet(dog)
    dog.add_task(Task("Breakfast", 10, "high", time="08:00"))
    dog.add_task(Task("Medication", 5, "high", time="08:00"))
    scheduler = Scheduler(owner)

    scheduler.generate_plan()

    assert len(scheduler.conflicts) == 1
    assert "Breakfast" in scheduler.conflicts[0]
    assert "Medication" in scheduler.conflicts[0]
    assert "08:00" in scheduler.conflicts[0]
