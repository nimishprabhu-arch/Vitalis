# Vitalis Coach Playbook

Use this file for detailed coaching patterns, examples, signal-combination logic, and reusable answer templates.

## Daily Coaching

_To be expanded._

## Recovery Coaching

_To be expanded._

## Lab + Lifestyle Coaching

_To be expanded._

## Trend Interpretation

_To be expanded._

## Freshness Lag Coaching

Always check freshness before interpreting time-sensitive metrics.

Guidance:
- If daily snapshot is current but Health Connect signals are stale, separate current scores from stale wearable metrics.
- Do not describe stale HR, sleep HR, SpO2, VO2, or workout data as today’s data.
- Say “latest available” when using older synced values.
- If freshness is mixed, give useful coaching from current fields but clearly state what is lagging.
- If a metric has not updated for several days, avoid strong day-specific conclusions from it.

## VO2 Max Coaching

Treat VO2 max as a long-term fitness estimate unless provenance says otherwise.

Guidance:
- Vitalis VO2 max currently comes from Samsung/Health Connect exported wearable data.
- It is not lab-measured and not Vitalis-estimated unless explicitly stated.
- Do not over-interpret one or two readings.
- Use VO2 max for long-term cardiorespiratory trend context, not daily coaching.
- Pair VO2 max with workout consistency, resting/daily HR, sleep HR, weight, and training history.

## Workout Coaching

Use workouts to judge training consistency, load, and recovery balance.

Guidance:
- Prefer workout duration, session count, exercise type, and workout HR when available.
- Weight training can show high HR and training load even without distance.
- Distance may be misleading when cycling or mixed activity is present.
- Exercise calories are part of active calories, not an additional category to add on top.
- Coach for consistency and recovery balance, not simply “more exercise.”
- If workout data is stale, say latest available workout data rather than implying current-day activity.

## Sleep HR Trend Coaching

Use sleep average heart rate as a recovery signal only when sample count is reasonably high. Prefer multi-night trends over single-night spikes.

Guidance:
- Lower sleep average HR versus recent baseline can suggest better recovery.
- Higher sleep average HR versus recent baseline can suggest stress, poor sleep, illness, alcohol, late meals, heat, or heavy training load.
- Treat low sample-count nights as lower confidence.
- Do not over-interpret single-night minimum or maximum HR.
- Always pair sleep HR with sleep duration, sleep quality, training load, and freshness status.

## SpO2 Confidence Coaching

Use SpO2 as a lower-confidence signal unless sample count is clearly adequate or the pattern repeats across multiple nights.

Guidance:
- One-sample SpO2 nights should be treated as sparse data, not a full overnight oxygen profile.
- Repeated low SpO2 values across multiple nights deserve more attention than one isolated value.
- Pair SpO2 with sleep quality, sleep HR, respiratory symptoms, snoring, alcohol, illness, altitude, and device fit.
- Do not diagnose sleep apnea or oxygen disorders from Vitalis data.
- If low values persist or symptoms are present, suggest clinician review or a proper sleep study.

## Regression Test Prompts

Use these prompts after GPT instruction, schema, endpoint, or knowledge-file changes.

Freshness:
1. Is my Vitalis sync fresh today?
2. Which Vitalis metrics are current and which are stale?
3. Can I rely on today's workout, sleep HR, SpO2, and VO2 data?

Coach intelligence:
4. What are my top 3 health priorities right now based on live Vitalis data and labs?
5. Give me today's coaching read using only live Vitalis data.
6. What should I do differently today based on readiness, recovery, sleep, workouts, and labs?

Heart rate and recovery:
7. How should I interpret my recent sleep heart rate trend?
8. Compare my daily HR and sleep HR signals.
9. Is my heart rate data reliable enough for recovery coaching?

SpO2 and VO2:
10. My SpO2 was 91% with one sample. Should I worry?
11. What does my VO2 max history show, and how reliable is it?
12. Is my VO2 max measured, estimated, or wearable-derived?

Workouts:
13. Compare my latest workout consistency with my recovery status.
14. Am I training too much, too little, or about right?
15. How should I interpret workout calories versus active calories?

Labs:
16. What lab results should I discuss with my doctor next?
17. What are my latest abnormal lab markers?
18. Compare my latest lipids with prior lipid reports.
19. Are my glucose and kidney markers reassuring?
20. Which lab values are missing, stale, or unavailable?