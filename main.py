from pawpal_system import Owner, Pet, Task, Scheduler


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

    # --- Define Tasks (added to each pet directly) ---
    morning_walk = Task(title="Morning walk",    duration_minutes=30, priority="high",   preferred_time="08:00", mandatory=True)
    feed_luna    = Task(title="Feed Luna",        duration_minutes=10, priority="high",   preferred_time="08:30", mandatory=True)
    brush_luna   = Task(title="Brush Luna",       duration_minutes=15, priority="low",    preferred_time="11:00", mandatory=False)
    litter_box   = Task(title="Clean litter box", duration_minutes=15, priority="medium", preferred_time="09:00", mandatory=True)
    playtime     = Task(title="Playtime with Mochi", duration_minutes=20, priority="low", preferred_time="10:00", mandatory=False)

    luna.add_task(morning_walk)
    luna.add_task(feed_luna)
    luna.add_task(brush_luna)
    mochi.add_task(litter_box)
    mochi.add_task(playtime)

    # --- Simulate task status updates ---
    feed_luna.mark_complete()       # already done — Scheduler will skip it
    morning_walk.mark_in_progress() # currently happening

    # --- Generate Plan ---
    scheduler = Scheduler()
    planner = scheduler.generate_plan(owner=owner)

    # --- Print Today's Schedule ---
    print("=" * 50)
    print(f"  Today's Schedule for {owner.name}")
    print("=" * 50)

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
    print()

    # --- Show already-complete tasks ---
    complete = [t for t in owner.get_all_tasks() if t.status == "complete"]
    if complete:
        print("  Already complete (skipped by scheduler):")
        for t in complete:
            print(f"    - {t.title}")

    # --- Show tasks dropped due to time budget ---
    if planner.skipped_tasks:
        print()
        print("  Skipped (did not fit in time budget):")
        for t in planner.skipped_tasks:
            print(f"    - {t.title} ({t.duration_minutes} min, {t.priority} priority)")

    print("=" * 50)


if __name__ == "__main__":
    main()
