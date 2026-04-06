# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Owner        - name: str
               free_minutes_per_day: int
               preferences: dict
               pets: list[Pet]
               Method:
                   update_preferences()

Pet          - name: str
               species: str

Task         - title: str
               duration_minutes: int
               priority: str
               preferred_time: str
               mandatory: bool
               Method:
                   get_priority()
                   edit_task()
                   add_task()

ScheduledTask - task: Task
                start_time: str
                end_time: str
                reason: str

DailyPlanner - owner: Owner
               pet: Pet
               scheduled_tasks: list[ScheduledTask]
               total_minutes: int
               Method:
                   add_scheduled_task()
                   get_reason()

Scheduler    - Method:
                   generate_plan(owner, pet, tasks)
                   sort_tasks(tasks)
                   explain_choice(task)



**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Added pet: pet = None to Task (line 15) because a task like "feed [pet name] should knwo which pet it belongs to. Wihtout this, there's is no way to filter or gorup tasks by pet. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

Time, prioirty, task status, pet fairness and we decided that mandatory status was raned above everything and is the most important as missing pet's medication or forgeting to feed is not good. 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

We chose priority as the primary sorting and time as secondary. This guarantees mandatory tasks always get scheduled. 

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

Actually implementing the logic in UI

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I think i would improve the UI

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important lesson was that designing for edge cases forces you to make your core logic explicit. And being as specific as possible. 
