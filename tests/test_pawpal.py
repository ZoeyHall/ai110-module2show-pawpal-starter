"""Tests for PawPal+ core classes."""

from datetime import date, timedelta

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
    import pytest

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
