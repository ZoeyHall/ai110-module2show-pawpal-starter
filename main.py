"""Demo script: build an owner with pets and tasks, then print sorted, filtered, and scheduled views."""

from pawpal_system import Owner, Pet, Task, Scheduler


def print_header(title: str) -> None:
    print("\n" + "=" * 55)
    print(title)
    print("=" * 55)


def print_tasks(tasks: list[Task]) -> None:
    if not tasks:
        print("  (none)")
        return
    for task in tasks:
        when = task.time or "Anytime"
        status = "done" if task.completed else "todo"
        print(
            f"  {task.due_date:%m/%d} {when:<8} {task.description:<20} "
            f"{task.pet_name:<8} {task.duration_minutes:>3} min  "
            f"[{task.priority}] {task.frequency:<6} {status}"
        )


def main() -> None:
    owner = Owner(name="Jordan", available_minutes=120)

    biscuit = Pet(name="Biscuit", species="dog", age=4)
    mochi = Pet(name="Mochi", species="cat", age=2)
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Tasks are added deliberately out of time order. "7:30" has no leading
    # zero, which a plain string sort would place after "17:00".
    mochi.add_task(Task("Laser pointer play", 25, "low", time="20:00"))
    biscuit.add_task(Task("Fetch in the yard", 20, "low", time="17:00"))
    mochi.add_task(Task("Clean litter box", 10, "medium"))
    biscuit.add_task(Task("Breakfast", 10, "high", time="08:00"))
    mochi.add_task(Task("Brush fur", 15, "medium", time="19:00"))
    biscuit.add_task(Task("Morning walk", 30, "high", time="7:30"))
    mochi.add_task(Task("Give medication", 5, "high", time="09:00", frequency="once"))
    biscuit.add_task(Task("Bath", 20, "medium", frequency="weekly"))

    # Deliberate conflicts: two pets at the same start time, and two tasks for
    # the same pet whose time slots overlap.
    mochi.add_task(Task("Breakfast", 10, "high", time="07:30"))
    biscuit.add_task(Task("Nail trim", 15, "medium", time="17:10"))

    scheduler = Scheduler(owner)

    print_header("All tasks, in the order they were added")
    print_tasks(owner.get_all_tasks())

    print_header("All tasks, sorted by time")
    print_tasks(scheduler.sort_by_time(owner.get_all_tasks()))

    # Complete a daily, a weekly, and a one-time task. The scheduler adds the
    # next occurrence for the repeating ones.
    print_header("Completing tasks")
    for pet, description in [
        (biscuit, "Breakfast"),
        (biscuit, "Bath"),
        (mochi, "Give medication"),
    ]:
        task = next(t for t in pet.tasks if t.description == description)
        next_task = scheduler.mark_task_complete(task)
        if next_task:
            print(f"  {description} ({task.frequency}) -> next due {next_task.due_date}")
        else:
            print(f"  {description} ({task.frequency}) -> does not repeat")

    print_header("Biscuit's tasks after completing, sorted by time")
    print_tasks(scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Biscuit")))

    print_header("Mochi's tasks, sorted by time")
    print_tasks(scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi")))

    print_header("Completed tasks")
    print_tasks(scheduler.filter_tasks(completed=True))

    plan = scheduler.generate_plan()
    print_header(f"Today's Schedule for {owner.name} (pending, due today)")
    print_tasks(plan)
    print(
        f"\n  Total: {scheduler.total_scheduled_minutes()} of "
        f"{owner.available_minutes} minutes"
    )
    if scheduler.skipped:
        print("\n  Skipped (not enough time):")
        for task in scheduler.skipped:
            print(f"  - {task.description} for {task.pet_name} ({task.duration_minutes} min)")

    print_header("Conflict check")
    if scheduler.conflicts:
        for warning in scheduler.conflicts:
            print(f"  {warning}")
    else:
        print("  No conflicts found.")


if __name__ == "__main__":
    main()
