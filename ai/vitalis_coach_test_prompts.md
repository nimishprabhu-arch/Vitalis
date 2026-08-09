# Vitalis Coach Test Prompts

Use these prompts to test whether the Vitalis GPT is using live actions correctly.

## Daily

1. How am I doing today? Use live Vitalis actions.

2. Summarize my day yesterday using live Vitalis data. Do not use knowledge files.

## Weekly

3. How am I doing this week? Compare the latest completed 7-day window with the previous 7-day window using live Vitalis actions.

4. Is my training load productive right now? Use live Vitalis actions.

## Monthly

5. Compare this month with last month using live Vitalis data.

6. What improved and worsened this month compared with last month?

## Historical

7. Compare 2026 with 2025 using live Vitalis data.

8. Compare 2026-08-07 with 2026-08-08 using live Vitalis data.

## Expected Behavior

The GPT should:
- Prefer live Vitalis actions over knowledge files.
- Use getDailyBriefMessage and getLatestSummaryMessage for current status.
- Use getSnapshotByDateMessage for date-specific questions.
- Use getComparePeriodsMessage for day/week/month/year comparisons.
- Use getLast30TrainingMessage for training recovery.
- Clearly say when today's data is incomplete.
- Give a simple verdict before details.