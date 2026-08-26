# Vitalis Coach Test Prompts

Use these prompts to test whether Vitalis GPT is using live actions, freshness rules, and coaching logic correctly.

## Freshness

1. Use live Vitalis only. Is my data fresh today?
2. Use live Vitalis only. Which metrics are latest available versus stale?
3. Use live Vitalis only. Can I trust today’s workout and HR data?

Expected:
- Uses fresh summary and/or freshness watchdog.
- Does not call older values “today.”
- Treats sleep HR and SpO₂ 1–2 day lag calmly.
- Flags true stale data clearly.

## Calories + Food

4. Use live Vitalis only. What is my calorie balance and macro gap today?
5. Use live Vitalis only. What should I eat next for lean-down?
6. Use live Vitalis only. Plan the rest of my day for lean-down.
7. Use live Vitalis only. If I correct a logged meal, should you update it or delete/recreate it?

Expected:
- Missing food is not zero intake.
- Missing burn is not zero burn.
- Uses macro balance for protein/fiber gaps.
- Gives Indian-friendly meal options.
- Updates existing food rows when row ID is known.

## Labs

8. Use live Vitalis only. Which lab tests are due next, why, and what should I do this week?
9. Use live Vitalis only. What is my GGT history and what does it mean?
10. Use live Vitalis only. What are my top 3 lab priorities?

Expected:
- Prioritizes GGT/liver, lipids, and persistent CBC patterns.
- Includes dates, values, flags, and source file when available.
- Does not say a marker is missing if marker history exists.
- Gives clinician-review caveat without diagnosing.

## Body Metrics

11. Use live Vitalis only. What is my latest weight and BP trend?
12. Use live Vitalis only. How should I use my weight trend to adjust lean-down calories?

Expected:
- Uses latest body metrics.
- Treats few readings as low confidence.
- Uses weekly trend, not one reading.
- Keeps BP advice cautious and non-diagnostic.

## Workouts + Recovery

13. Use live Vitalis only. Is my training productive right now?
14. Use live Vitalis only. Summarize my latest workouts.
15. Use live Vitalis only. Should I train hard today or keep it light?

Expected:
- Uses fresh workout snapshot for today-level coaching.
- Uses workout table for detailed history.
- Combines readiness, recovery, training load, sleep, and HR.
- Does not treat missing detailed workout rows as no workout if snapshot is fresh.