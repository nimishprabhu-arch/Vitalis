# Vitalis Metric Glossary

Use this file for definitions, provenance, units, and interpretation caveats. Live Vitalis data remains the source of truth.

## Freshness

- `fresh_vitalis_summary`: source router for the freshest usable value per metric.
- `freshness_watchdog`: freshness status by signal.
- Fresh: 0–1 days behind.
- Slightly delayed: 2–3 days behind.
- Stale: more than 3 days behind.
- Sleep HR and SpO₂ may naturally lag by about 1–2 days.

## Daily Snapshot Metrics

- `snapshot_date`: date represented by the snapshot.
- `source`: source that last updated the row, such as `vitalis_android` or `health_connect_cloud_sync`.
- `steps`: daily step count.
- `distance_meters`: distance in meters; may be direct or estimated depending on source.
- `average_heart_rate`, `minimum_heart_rate`, `maximum_heart_rate`: older/day summary HR fields; secondary when `daily_hr_*` exists.
- `daily_hr_average`, `daily_hr_minimum`, `daily_hr_maximum`, `daily_hr_sample_count`: full-day Health Connect HR rollup. Prefer these for daytime HR trends.
- `resting_heart_rate`: resting HR when available.

## Sleep Metrics

- `sleep_total_minutes`: total sleep duration.
- `deep_sleep_minutes`, `rem_sleep_minutes`, `light_sleep_minutes`, `awake_minutes`: sleep-stage breakdown when available.
- `sleep_session_count`: number of sleep sessions.
- `sleep_score`: Samsung/Vitalis sleep score when available.
- `sleep_average_heart_rate`, `sleep_minimum_heart_rate`, `sleep_maximum_heart_rate`, `sleep_heart_rate_sample_count`: sleep-window HR rollup. Average and sample count are more useful than min/max extremes.

## Oxygen + Fitness

- `spo2_average`, `spo2_minimum`, `spo2_maximum`, `spo2_sample_count`: Health Connect/Samsung exported oxygen saturation fields. Single-sample values are low confidence.
- `vo2_max`: Samsung/Health Connect wearable-estimated VO₂ max. It is not lab-measured and not Vitalis-estimated.

## Calories + Food

- `active_calories`: activity calories from source data.
- `rest_calories`: resting/basal calories when available.
- `exercise_calories`: exercise/workout calorie component; do not add on top of active or total burn unless explicitly defined by source logic.
- `total_burned_calories`: best measured total daily burn when available.
- `workout_total_calories`: workout burn only, not total daily expenditure.
- `daily_calorie_balance`: intake minus burn for one date.
- `weekly_calorie_balance`: calorie balance across days with both food and burn data.
- `macro_balance`: protein/fiber/calorie gap against current goal.
- Fallback resting burn: about 1643 kcal/day, estimated from Mifflin-St Jeor using roughly 79 kg, 170 cm, age 43, male.

## Workout Metrics

- `workout_session_count`: number of workout sessions for the day.
- `workout_total_duration_minutes`: total workout minutes for the day.
- `workout_total_calories`: measured workout calories when available.
- `workout_distance_meters`: workout distance when available.
- `workout_average_heart_rate`, `workout_minimum_heart_rate`, `workout_maximum_heart_rate`: workout HR metrics when available.
- HR zone minutes: low intensity, weight control, aerobic, anaerobic, and max intensity minutes.

## Vitalis Scores

- `vitalis_readiness_score`: Vitalis-derived readiness score.
- `vitalis_sleep_quality_score`: Vitalis-derived sleep quality score.
- `vitalis_recovery_score`: Vitalis-derived recovery score.
- `vitalis_training_load_score`: Vitalis-derived training load score.
- `vitalis_coach_note`: generated coach note from Vitalis logic.
- These are Vitalis-derived scores, not Samsung scores.

## Body Metrics

- `weight_kg`: manual body weight entry.
- `systolic_bp`, `diastolic_bp`: manual blood pressure entry.
- `waist_cm`: optional waist circumference if tracked.
- Body metrics are most useful as weekly trends under similar conditions.

## Lab Metrics

- `test_date`: date of the lab test; use this for recency.
- `category`: lab group such as Lipids, Liver, CBC, Kidney, Thyroid, Glucose, Vitamins.
- `marker`: canonical lab marker name.
- `value`, `unit`: parsed result and unit.
- `reference_low`, `reference_high`: reference interval when parsed.
- `flag`: normal, high, low, abnormal, or similar parsed flag.
- `source_file`: original report file.
- Lab parsing is automated; verify against original reports for medical decisions.