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
    luna.add_task(Task(
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        preferred_time="08:00",
        mandatory=True,
    ))
    luna.add_task(Task(
        title="Feed Luna",
        duration_minutes=10,
        priority="high",
        preferred_time="08:30",
        mandatory=True,
    ))
    luna.add_task(Task(
        title="Brush Luna",
        duration_minutes=15,
        priority="low",
        preferred_time="11:00",
        mandatory=False,
    ))

    mochi.add_task(Task(
        title="Clean Mochi's litter box",
        duration_minutes=15,
        priority="medium",
        preferred_time="09:00",
        mandatory=True,
    ))
    mochi.add_task(Task(
        title="Playtime with Mochi",
        duration_minutes=20,
        priority="low",
        preferred_time="10:00",
        mandatory=False,
    ))

    # --- Generate Plan ---
    scheduler = Scheduler()
    planner = scheduler.generate_plan(owner=owner)

    # --- Print Today's Schedule ---
    print("=" * 45)
    print(f"  Today's Schedule for {owner.name}")
    print("=" * 45)

    if not planner.scheduled_tasks:
        print("  No tasks could be scheduled today.")
    else:
        for st in planner.scheduled_tasks:
            pet_label = f"[{st.task.pet.name}]" if st.task.pet else ""
            print(f"  {st.start_time} – {st.end_time}  {st.task.title} {pet_label}")
            print(f"    Reason: {st.reason}")

    print("-" * 45)
    print(f"  Total scheduled: {planner.total_minutes} / {owner.free_minutes_per_day} minutes")
    print("=" * 45)


if __name__ == "__main__":
    main()
