from pawpal_system import Owner, Pet, Task, Scheduler


def print_section(title: str) -> None:
    print()
    print("=" * 50)
    print(f"  {title}")
    print("=" * 50)


def main():
    # --- Setup Owner ---
    owner = Owner(
        name="Alex",
        free_minutes_per_day=120,
        preferences={"preferred_start": "morning", "skip_weekends": False},
    )

    # --- Setup Pets ---
    luna = Pet(name="Luna", species="Dog")
    mochi = Pet(name="Mochi", species="Cat")

    owner.add_pet(luna)
    owner.add_pet(mochi)

    # --- Add tasks intentionally out of order ---
    # Low priority and late time added first, high priority and early time added last
    brush_luna   = Task(title="Brush Luna",          duration_minutes=15, priority="low",    preferred_time="11:00", mandatory=False, recurrence="weekly")
    playtime     = Task(title="Playtime with Mochi", duration_minutes=20, priority="low",    preferred_time="10:00", mandatory=False)
    litter_box   = Task(title="Clean litter box",    duration_minutes=15, priority="medium", preferred_time="09:00", mandatory=True,  recurrence="daily")
    feed_luna    = Task(title="Feed Luna",            duration_minutes=10, priority="high",   preferred_time="08:30", mandatory=True,  recurrence="daily")
    morning_walk = Task(title="Morning walk",         duration_minutes=30, priority="high",   preferred_time="08:00", mandatory=True)

    luna.add_task(brush_luna)    # low / 11:00  — added first intentionally
    mochi.add_task(playtime)     # low / 10:00
    mochi.add_task(litter_box)   # medium / 09:00
    luna.add_task(feed_luna)     # high / 08:30
    luna.add_task(morning_walk)  # high / 08:00  — added last intentionally

    # --- Simulate status updates ---
    feed_luna.mark_complete()        # daily recurring — should spawn a new instance
    morning_walk.mark_in_progress()  # currently happening

    # ------------------------------------------------------------------
    # FILTER DEMOS
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # RECURRENCE DEMO
    # ------------------------------------------------------------------

    print_section("Recurrence: Luna's tasks BEFORE marking Feed Luna complete")
    for t in luna.get_tasks():
        recur_label = f"recurrence={t.recurrence}" if t.recurrence else "no recurrence"
        print(f"  {t.title:<25} status={t.status:<12} {recur_label}")

    print()
    print("  >>> feed_luna.mark_complete() called <<<")

    print_section("Recurrence: Luna's tasks AFTER marking Feed Luna complete")
    for t in luna.get_tasks():
        recur_label = f"recurrence={t.recurrence}" if t.recurrence else "no recurrence"
        print(f"  {t.title:<25} status={t.status:<12} {recur_label}")

    print()
    print("  Feed Luna (complete) — original instance, will be skipped by scheduler")
    print("  Feed Luna (incomplete) — new instance spawned automatically, ready to schedule")

    # ------------------------------------------------------------------
    # FILTER DEMOS
    # ------------------------------------------------------------------

    print_section("Filter: All tasks (unsorted, insertion order)")
    for t in owner.get_all_tasks():
        pet_label = t.pet.name if t.pet else "—"
        print(f"  [{pet_label}] {t.title:<25} {t.priority:<8} {t.preferred_time}  status={t.status}")

    print_section("Filter: owner.filter_tasks(status='complete')")
    for t in owner.filter_tasks(status="complete"):
        print(f"  {t.title} [{t.pet.name if t.pet else '—'}]")

    print_section("Filter: owner.filter_tasks(status='incomplete')")
    for t in owner.filter_tasks(status="incomplete"):
        print(f"  {t.title} [{t.pet.name if t.pet else '—'}]")

    print_section("Filter: owner.filter_tasks(pet_name='Luna')")
    for t in owner.filter_tasks(pet_name="Luna"):
        print(f"  {t.title:<25} status={t.status}")

    print_section("Filter: owner.filter_tasks(status='incomplete', pet_name='Luna')")
    for t in owner.filter_tasks(status="incomplete", pet_name="Luna"):
        print(f"  {t.title}")

    print_section("Filter: luna.filter_tasks(status='complete')")
    for t in luna.filter_tasks(status="complete"):
        print(f"  {t.title}")

    # ------------------------------------------------------------------
    # SORT DEMO — tasks sorted before scheduling
    # ------------------------------------------------------------------
    scheduler = Scheduler()

    print_section("Sort: sort_tasks() output (priority → time → duration)")
    for t in scheduler.sort_tasks(owner.get_all_tasks()):
        mandatory_label = "mandatory" if t.mandatory else "optional "
        print(f"  [{mandatory_label}] {t.priority:<8} {t.preferred_time}  {t.title}")

    # ------------------------------------------------------------------
    # SCHEDULE
    # ------------------------------------------------------------------
    planner = scheduler.generate_plan(owner=owner)

    print_section(f"Today's Schedule for {owner.name}")
    if not planner.scheduled_tasks:
        print("  No tasks could be scheduled today.")
    else:
        for st in planner.scheduled_tasks:
            pet_label = f"[{st.task.pet.name}]" if st.task.pet else ""
            print(f"  {st.start_time} – {st.end_time}  {st.task.title} {pet_label}")
            print(f"    Status: {st.task.status}")
            print(f"    Reason: {st.reason}")

    print("-" * 50)
    print(f"  Total scheduled: {planner.total_minutes} / {owner.free_minutes_per_day} minutes")

    if owner.filter_tasks(status="complete"):
        print()
        print("  Already complete (skipped by scheduler):")
        for t in owner.filter_tasks(status="complete"):
            print(f"    - {t.title}")

    if planner.skipped_tasks:
        print()
        print("  Skipped (did not fit in time budget):")
        for t in planner.skipped_tasks:
            print(f"    - {t.title} ({t.duration_minutes} min, {t.priority} priority)")

    print("=" * 50)


if __name__ == "__main__":
    main()
