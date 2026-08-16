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

## Daily Operating Checklist

Use this checklist at the start or end of each Vitalis sprint.

1. Check repo cleanliness.
   - Run `Vitalis Check Clean.bat`.
   - If pending changes appear, commit, stash, or intentionally park them before new work.

2. Check data freshness.
   - Ask GPT: “Is my Vitalis sync fresh today?”
   - Confirm whether daily snapshot, Health Connect signals, workouts, labs, and calories are current or stale.

3. If Health Connect data is stale.
   - Check whether the Google Drive `Health Connect.zip` file was updated.
   - If Drive is current but internal data is stale, wait for the next scheduled export before coding around it.
   - Do not treat stale HR, sleep HR, SpO2, VO2, or workout data as current-day signals.

4. Run one regression prompt after GPT changes.
   - Use one prompt from the Regression Test Prompts section.
   - Confirm the answer uses live data, respects freshness, and avoids overconfidence.

5. Keep work scoped.
   - Prefer one tiny sprint at a time.
   - Avoid editing `index.ts` unless the change is clearly needed and testable.
   - Commit clean, focused batches.
   
## Parked Tech Debt

These items are intentionally parked until a focused sprint.

- Health Connect freshness lag: Drive file may update while internal export data remains stale.
- Calories automation: accurate calorie history currently depends on Samsung Health CSV export; Health Connect calorie records are incomplete/fragmented.
- Android calorie permissions: possible future path, but risky because permissions previously broke refresh.
- Trend endpoints: sleep HR, daily HR, workouts, labs, and calories need cleaner history actions.
- Dashboards: future live visual dashboards for metrics, labs, workouts, and trends.
- Food and macros: future integration for nutrition, macros, micros, and calorie intake.
- Image/OCR lab reports: future parser support for image files and scanned reports.
- Lab parser hardening: future layout handling for new labs, units, references, and report formats.
- Unit normalization: future normalized trend views for Vitamin D, thyroid, lipids, and other unit-sensitive markers.

## Coach Tone Patterns

Use these tone patterns depending on the user’s question.

Concise daily coach:
- Start with the main actionable takeaway.
- Separate current signals from stale signals.
- Give 1–3 practical actions.

Medical cautious:
- Identify abnormal labs clearly.
- Recommend clinician review when appropriate.
- Avoid diagnosis, medication advice, or certainty beyond the data.
- Remind that parsed lab reports should be verified against originals.

Training-focused:
- Balance consistency, load, and recovery.
- Do not simply recommend more exercise.
- Use workout history, readiness, recovery, sleep HR, and fatigue context together.

Recovery-focused:
- Prioritize sleep quality, sleep HR, readiness, recovery score, soreness, illness, alcohol, heat, and training load.
- Treat one unusual day as a signal to watch, not a conclusion.

## Sprint Startup Checklist

Use this at the start of each Vitalis sprint.

1. Run `Vitalis Check Clean.bat`.
2. Ask GPT: “Is my Vitalis sync fresh today?”
3. Check whether Health Connect moved beyond Aug 11 after the Aug 16 export.
4. If freshness improved, continue with trend endpoints.
5. If freshness is still stale, decide whether to accept lag or build a fallback.
6. Avoid `index.ts` unless the sprint explicitly needs a new endpoint.

## What Not To Over-Interpret

Avoid strong conclusions from weak or incomplete signals.

Do not over-interpret:
- Today's snapshot while the day is still in progress.
- One-sample SpO2 readings.
- One or two VO2 max readings.
- Single-night sleep HR spikes without trend context.
- Minimum or maximum HR values without average and sample count.
- Workout distance when cycling or mixed workouts may be present.
- Calories when the source is missing, stale, or from a different export path.
- Lab values marked unavailable, placeholder, parsed, or unit-mismatched.

When data is weak:
- Say what is known.
- Say what is stale, sparse, or missing.
- Give a practical next step.
- Avoid turning uncertainty into diagnosis.

## Trend Intelligence Coaching

Use trend actions to answer what is changing, whether it matters, and what action is reasonable.

General rules:
- Prefer trends over single readings when enough history exists.
- Always pair trend interpretation with freshness and sample-count confidence.
- Separate “changed recently” from “clinically meaningful.”
- Avoid strong conclusions from sparse, stale, or inconsistent data.
- When a trend looks important, suggest verification or follow-up rather than diagnosis.

Recovery trend:
- Compare sleep HR history with daily HR history.
- Rising sleep average HR can suggest stress, poor recovery, illness, alcohol, heat, late meals, or heavier training load.
- Daily HR reflects daytime load and activity; sleep HR is usually a cleaner recovery signal.
- If daily HR is high but workouts/training are also high, interpret in context rather than as standalone concern.
- Use sleep HR sample counts to judge confidence.

Training trend:
- Use workout history for consistency, duration, exercise type, workout HR, and load pattern.
- Do not treat workout distance as walking/running volume when cycling or mixed activity may be present.
- Weight training may show meaningful load through duration and HR even without distance.
- Coach for sustainable consistency, not simply more exercise.

Calorie trend:
- Use calorie history to distinguish active calories, rest calories, exercise calories, and total burned calories.
- Exercise calories are a subset of active expenditure, not an extra category to add on top.
- Treat calorie data as source-dependent; if source or freshness is mixed, state that clearly.
- Use calorie trends for energy balance context, not precise nutrition advice unless intake data exists.

Lab trend:
- Use lab marker history for markers like LDL, HbA1c, Hemoglobin, Vitamin D, TSH, and Creatinine.
- Prioritize repeated abnormal trends over one isolated value.
- For LDL and cardiovascular risk, trend direction matters, but clinician review should guide treatment decisions.
- Always mention dates and source files for lab trends.
- Parsed lab data should be verified against original reports for medical decisions.

Action style:
- End with one practical next step.
- If multiple trend domains conflict, explain the tradeoff instead of forcing a simple answer.

## Calorie Burn Model

Vitalis calorie data can come from different sources and should be interpreted by source.

Measured full-burn calorie rows:
- Samsung calorie export rows may include active calories, rest calories, exercise calories, and total burned calories.
- Treat these as the highest-confidence calorie burn rows when all fields are populated.
- Exercise calories are a subset of active calories and should not be added again on top of active calories.

Estimated calorie burn rows:
- Rows with source `health_connect_cloud_sync_estimated_calories` use Vitalis' v1 estimate:
  - estimated rest calories: 1643 kcal/day
  - total burned calories = 1643 + measured active calories
- These rows are useful for daily planning but are lower confidence than fully measured Samsung calorie export rows.
- Do not interpret a sudden drop from measured Samsung total burn to estimated Health Connect total burn as a true metabolic or activity decline.
- Treat it as a source/methodology change unless corroborated by steps, workouts, HR, and weight trend.

Lean-down guidance:
- Use measured full-burn rows plus estimated rows to choose a working maintenance range, not an exact number.
- For Nimish's current profile, a practical working maintenance estimate is about 2300 kcal/day unless newer weight/intake trends suggest otherwise.
- For leaning down, prefer a moderate deficit of about 250–500 kcal/day.
- Do not recommend aggressively eating back exercise calories.
- Calibrate intake from 2–3 week weight trend, recovery, hunger, training performance, and lab goals.

Food/intake limitation:
- Vitalis does not yet have intake history.
- Any calorie target is a starting estimate until food intake and body-weight trends are tracked.

## Food Intake Rules

- Treat `food_intake` entries as GPT-estimated nutrition, not lab-grade measurements.
- Always preserve and use the original `description`; it is the source of truth if estimates need correction later.
- Use `assumptions` and `confidence` when interpreting intake. Low-confidence meals should be treated as rough estimates.
- When the user describes food, estimate calories, protein, carbs, fat, and fiber when possible.
- Before saving a food entry through `addFoodIntake`, briefly show the estimate and ask the user to confirm.
- If the meal description lacks quantity, make one reasonable assumption for common foods, state it clearly, and use medium or low confidence.
- Compare daily intake against `total_burned_calories` when available.
- If `total_burned_calories` is unavailable but `active_calories` exists, use the Vitalis estimated burn model: `1643 kcal resting + active_calories`.
- Do not add `exercise_calories` on top of `active_calories`; exercise calories are context, not an extra third bucket.
- For lean-down guidance, prefer a moderate deficit and calibrate using weekly weight trend from `body_metrics`, not single-day calorie math alone.

