const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const TABLE = "health_snapshots";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    },
  });
}

async function supabaseGet(path: string) {
  const response = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    headers: {
      apikey: SUPABASE_SERVICE_ROLE_KEY,
      Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Supabase ${response.status}: ${await response.text()}`);
  }

  return await response.json();
}

async function supabaseUpsertSnapshot(snapshot: Record<string, unknown>) {
  const response = await fetch(
    `${SUPABASE_URL}/rest/v1/${TABLE}?on_conflict=snapshot_date`,
    {
      method: "POST",
      headers: {
        apikey: SUPABASE_SERVICE_ROLE_KEY,
        Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        "Content-Type": "application/json",
        Prefer: "resolution=merge-duplicates,return=representation",
      },
      body: JSON.stringify(snapshot),
    }
  );

  const body = await response.text();

  if (!response.ok) {
    throw new Error(`Supabase ${response.status}: ${body}`);
  }

  return body ? JSON.parse(body) : [];
}

function round(value: unknown, digits = 2) {
  if (value === null || value === undefined || value === "") return null;
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) return null;
  return Number(numberValue.toFixed(digits));
}

function integerOrNull(value: unknown) {
  if (value === null || value === undefined || value === "") return null;
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) return null;
  return Math.round(numberValue);
}

function realOrNull(value: unknown) {
  if (value === null || value === undefined || value === "") return null;
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) return null;
  return numberValue;
}

function textOrNull(value: unknown) {
  if (value === null || value === undefined || value === "") return null;
  return String(value);
}

function formatMinutes(value: unknown) {
  if (value === null || value === undefined) return null;
  const total = Math.round(Number(value));
  if (Number.isNaN(total)) return null;

  const hours = Math.floor(total / 60);
  const minutes = total % 60;

  if (hours <= 0) return `${minutes}m`;
  if (minutes === 0) return `${hours}h`;
  return `${hours}h ${minutes}m`;
}

function average(rows: any[], field: string) {
  const values = rows
    .map((row) => row[field])
    .filter((value) => value !== null && value !== undefined)
    .map(Number)
    .filter((value) => !Number.isNaN(value));

  if (values.length === 0) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function sum(rows: any[], field: string) {
  return rows
    .map((row) => row[field])
    .filter((value) => value !== null && value !== undefined)
    .map(Number)
    .filter((value) => !Number.isNaN(value))
    .reduce((total, value) => total + value, 0);
}

function pick(payload: Record<string, unknown>, snakeName: string, camelName: string) {
  return payload[snakeName] ?? payload[camelName] ?? null;
}

function normalizeSnapshot(payload: Record<string, unknown>) {
  const snapshotDate = pick(payload, "snapshot_date", "date");
  const savedAt = pick(payload, "saved_at", "savedAt") ?? new Date().toISOString();

  if (!snapshotDate) {
    throw new Error("Missing required field: snapshot_date");
  }

  return {
    snapshot_date: textOrNull(snapshotDate),
    saved_at: textOrNull(savedAt),
    steps: integerOrNull(pick(payload, "steps", "steps")),
    distance_meters: realOrNull(pick(payload, "distance_meters", "distanceMeters")),
    active_calories: realOrNull(pick(payload, "active_calories", "activeCalories")),
    floors: realOrNull(pick(payload, "floors", "floors")),
    average_heart_rate: realOrNull(pick(payload, "average_heart_rate", "averageHeartRate")),
    minimum_heart_rate: integerOrNull(pick(payload, "minimum_heart_rate", "minimumHeartRate")),
    maximum_heart_rate: integerOrNull(pick(payload, "maximum_heart_rate", "maximumHeartRate")),
    resting_heart_rate: integerOrNull(pick(payload, "resting_heart_rate", "restingHeartRate")),
    sleep_total_minutes: integerOrNull(pick(payload, "sleep_total_minutes", "sleepTotalMinutes")),
    deep_sleep_minutes: integerOrNull(pick(payload, "deep_sleep_minutes", "deepSleepMinutes")),
    rem_sleep_minutes: integerOrNull(pick(payload, "rem_sleep_minutes", "remSleepMinutes")),
    light_sleep_minutes: integerOrNull(pick(payload, "light_sleep_minutes", "lightSleepMinutes")),
    awake_minutes: integerOrNull(pick(payload, "awake_minutes", "awakeMinutes")),
    sleep_session_count: integerOrNull(pick(payload, "sleep_session_count", "sleepSessionCount")),
    workout_session_count: integerOrNull(pick(payload, "workout_session_count", "workoutSessionCount")),
    workout_total_duration_minutes: integerOrNull(
      pick(payload, "workout_total_duration_minutes", "workoutTotalDurationMinutes")
    ),
    sleep_score: realOrNull(pick(payload, "sleep_score", "sleepScore")),
    sleep_efficiency: realOrNull(pick(payload, "sleep_efficiency", "sleepEfficiency")),
    physical_recovery: realOrNull(pick(payload, "physical_recovery", "physicalRecovery")),
    mental_recovery: realOrNull(pick(payload, "mental_recovery", "mentalRecovery")),
    energy_score: realOrNull(pick(payload, "energy_score", "energyScore")),
    energy_sleep_score: realOrNull(pick(payload, "energy_sleep_score", "energySleepScore")),
    energy_activity_score: realOrNull(pick(payload, "energy_activity_score", "energyActivityScore")),
    heart_health_score: realOrNull(pick(payload, "heart_health_score", "heartHealthScore")),
	vitalis_readiness_score: integerOrNull(pick(payload, "vitalis_readiness_score", "vitalisReadinessScore")),
vitalis_sleep_quality_score: integerOrNull(pick(payload, "vitalis_sleep_quality_score", "vitalisSleepQualityScore")),
vitalis_recovery_score: integerOrNull(pick(payload, "vitalis_recovery_score", "vitalisRecoveryScore")),
vitalis_training_load_score: integerOrNull(pick(payload, "vitalis_training_load_score", "vitalisTrainingLoadScore")),
vitalis_coach_note: textOrNull(pick(payload, "vitalis_coach_note", "vitalisCoachNote")),
    source: textOrNull(pick(payload, "source", "source")) ?? "vitalis_android",
  };
}

async function getLatestRow() {
  const rows = await supabaseGet(`${TABLE}?select=*&order=snapshot_date.desc&limit=1`);
  return rows?.[0] ?? null;
}

async function getRecentRows(days: number) {
  const rows = await supabaseGet(`${TABLE}?select=*&order=snapshot_date.desc&limit=${days}`);
  return Array.isArray(rows) ? rows : [];
}

async function getRange() {
  const firstRows = await supabaseGet(
    `${TABLE}?select=snapshot_date&order=snapshot_date.asc&limit=1`
  );

  const latestRows = await supabaseGet(
    `${TABLE}?select=snapshot_date&order=snapshot_date.desc&limit=1`
  );

  const countResponse = await fetch(
    `${SUPABASE_URL}/rest/v1/${TABLE}?select=snapshot_date&limit=1`,
    {
      headers: {
        apikey: SUPABASE_SERVICE_ROLE_KEY,
        Authorization: `Bearer ${SUPABASE_SERVICE_ROLE_KEY}`,
        Prefer: "count=exact",
      },
    }
  );

  const contentRange = countResponse.headers.get("content-range");
  const totalSnapshots = contentRange?.split("/")?.[1] ?? null;

  return {
    status: "ok",
    first_date: firstRows?.[0]?.snapshot_date ?? null,
    latest_date: latestRows?.[0]?.snapshot_date ?? null,
    total_snapshots: totalSnapshots ? Number(totalSnapshots) : null,
  };
}

async function getSnapshotByDate(snapshotDate: string) {
  const rows = await supabaseGet(
    `${TABLE}?select=*&snapshot_date=eq.${encodeURIComponent(snapshotDate)}&limit=1`
  );

  const row = rows?.[0] ?? null;

  return {
    status: row ? "ok" : "empty",
    snapshot: row,
  };
}

function snapshotMessageLines(snapshot: any) {
  return [
    `snapshot_date: ${snapshot.snapshot_date}`,
    `steps: ${snapshot.steps}`,
    `distance_meters: ${round(snapshot.distance_meters)}`,
    `active_calories: ${round(snapshot.active_calories)}`,
    `average_heart_rate: ${round(snapshot.average_heart_rate)}`,
    `minimum_heart_rate: ${snapshot.minimum_heart_rate}`,
    `maximum_heart_rate: ${snapshot.maximum_heart_rate}`,
    `resting_heart_rate: ${snapshot.resting_heart_rate}`,
    `sleep_total_minutes: ${snapshot.sleep_total_minutes}`,
    `deep_sleep_minutes: ${snapshot.deep_sleep_minutes}`,
    `rem_sleep_minutes: ${snapshot.rem_sleep_minutes}`,
    `light_sleep_minutes: ${snapshot.light_sleep_minutes}`,
    `awake_minutes: ${snapshot.awake_minutes}`,
    `sleep_session_count: ${snapshot.sleep_session_count}`,
    `sleep_score: ${round(snapshot.sleep_score)}`,
    `energy_score: ${round(snapshot.energy_score)}`,
    `energy_sleep_score: ${round(snapshot.energy_sleep_score)}`,
    `energy_activity_score: ${round(snapshot.energy_activity_score)}`,
    `workout_session_count: ${snapshot.workout_session_count}`,
    `workout_total_duration_minutes: ${snapshot.workout_total_duration_minutes}`,
    `vitalis_readiness_score: ${snapshot.vitalis_readiness_score}`,
    `vitalis_sleep_quality_score: ${snapshot.vitalis_sleep_quality_score}`,
    `vitalis_recovery_score: ${snapshot.vitalis_recovery_score}`,
    `vitalis_training_load_score: ${snapshot.vitalis_training_load_score}`,
    `vitalis_coach_note: ${snapshot.vitalis_coach_note}`,
    `source: ${snapshot.source}`,
  ];
}

function parsePeriod(period: string) {
  if (period.includes("..")) {
    const [start, end] = period.split("..");
    return { start, end };
  }

  if (/^\d{4}-\d{2}-\d{2}$/.test(period)) {
    return { start: period, end: period };
  }

  if (/^\d{4}-\d{2}$/.test(period)) {
    const [year, month] = period.split("-").map(Number);
    const endDate = new Date(Date.UTC(year, month, 0));
    return {
      start: `${period}-01`,
      end: endDate.toISOString().slice(0, 10),
    };
  }

  if (/^\d{4}$/.test(period)) {
    return {
      start: `${period}-01-01`,
      end: `${period}-12-31`,
    };
  }

  throw new Error(`Invalid period: ${period}`);
}

async function getRowsForPeriod(period: string) {
  const range = parsePeriod(period);

  const rows = await supabaseGet(
    `${TABLE}?select=*&snapshot_date=gte.${range.start}&snapshot_date=lte.${range.end}&order=snapshot_date.asc`
  );

  return {
    period,
    start: range.start,
    end: range.end,
    rows: rows ?? [],
  };
}



function periodSummary(periodData: any) {
  const rows = periodData.rows;

  return {
    period: periodData.period,
    start: periodData.start,
    end: periodData.end,
    days: rows.length,
    total_steps: sum(rows, "steps"),
    average_steps: average(rows, "steps"),
    average_sleep_minutes: average(rows, "sleep_total_minutes"),
    average_heart_rate: average(rows, "average_heart_rate"),
    average_readiness: average(rows, "vitalis_readiness_score"),
    average_sleep_quality: average(rows, "vitalis_sleep_quality_score"),
    average_recovery: average(rows, "vitalis_recovery_score"),
    average_training_load: average(rows, "vitalis_training_load_score"),
    workout_days: rows.filter((row) => Number(row.workout_session_count ?? 0) > 0).length,
    workout_duration_minutes: sum(rows, "workout_total_duration_minutes"),
  };
}

function difference(valueB: number | null, valueA: number | null) {
  if (valueA === null || valueB === null) return null;
  return round(valueB - valueA);
}

function compareMessageLines(summaryA: any, summaryB: any) {
  return [
    `period_a: ${summaryA.period}`,
    `period_b: ${summaryB.period}`,
    `period_a_range: ${summaryA.start}..${summaryA.end}`,
    `period_b_range: ${summaryB.start}..${summaryB.end}`,
    `period_a_days: ${summaryA.days}`,
    `period_b_days: ${summaryB.days}`,
    `period_a_total_steps: ${summaryA.total_steps}`,
    `period_b_total_steps: ${summaryB.total_steps}`,
    `average_steps_change: ${difference(summaryB.average_steps, summaryA.average_steps)}`,
    `average_sleep_change_minutes: ${difference(summaryB.average_sleep_minutes, summaryA.average_sleep_minutes)}`,
    `average_heart_rate_change: ${difference(summaryB.average_heart_rate, summaryA.average_heart_rate)}`,
    `readiness_change: ${difference(summaryB.average_readiness, summaryA.average_readiness)}`,
    `sleep_quality_change: ${difference(summaryB.average_sleep_quality, summaryA.average_sleep_quality)}`,
    `recovery_change: ${difference(summaryB.average_recovery, summaryA.average_recovery)}`,
    `training_load_change: ${difference(summaryB.average_training_load, summaryA.average_training_load)}`,
    `workout_days_change: ${summaryB.workout_days - summaryA.workout_days}`,
    `workout_duration_change_minutes: ${round(summaryB.workout_duration_minutes - summaryA.workout_duration_minutes)}`,
  ];
}

async function comparePeriods(periodA: string, periodB: string) {
  const dataA = await getRowsForPeriod(periodA);
  const dataB = await getRowsForPeriod(periodB);

  return {
    summaryA: periodSummary(dataA),
    summaryB: periodSummary(dataB),
  };
}

async function getLatestSummary() {
  const row = await getLatestRow();

  return {
    status: row ? "ok" : "empty",
    latest_summary: row
      ? {
          snapshot_date: row.snapshot_date,
          saved_at: row.saved_at,
          steps: row.steps,
          distance_meters: round(row.distance_meters),
          active_calories: round(row.active_calories),
          floors: row.floors,
          average_heart_rate: round(row.average_heart_rate),
          minimum_heart_rate: row.minimum_heart_rate,
          maximum_heart_rate: row.maximum_heart_rate,
          resting_heart_rate: row.resting_heart_rate,
          sleep_total_minutes: row.sleep_total_minutes,
          deep_sleep_minutes: row.deep_sleep_minutes,
          rem_sleep_minutes: row.rem_sleep_minutes,
          light_sleep_minutes: row.light_sleep_minutes,
          awake_minutes: row.awake_minutes,
          sleep_session_count: row.sleep_session_count,
          sleep_score: round(row.sleep_score),
          sleep_efficiency: round(row.sleep_efficiency),
          physical_recovery: round(row.physical_recovery),
          mental_recovery: round(row.mental_recovery),
          energy_score: round(row.energy_score),
          energy_sleep_score: round(row.energy_sleep_score),
          energy_activity_score: round(row.energy_activity_score),
          heart_health_score: round(row.heart_health_score),
          workout_session_count: row.workout_session_count,
          workout_total_duration_minutes: row.workout_total_duration_minutes,
		  vitalis_readiness_score: row.vitalis_readiness_score,
			vitalis_sleep_quality_score: row.vitalis_sleep_quality_score,
			vitalis_recovery_score: row.vitalis_recovery_score,
			vitalis_training_load_score: row.vitalis_training_load_score,
			vitalis_coach_note: row.vitalis_coach_note,
		  
		  
          source: row.source,
        }
      : null,
  };
}

async function getDailyBrief() {
  const latest = await getLatestRow();

  if (!latest) {
    return { status: "empty", daily_brief: null };
  }

  const notes: string[] = [];

  if ((latest.steps ?? 0) >= 8000) notes.push("Strong step count.");
  else if ((latest.steps ?? 0) >= 5000) notes.push("Moderate movement day.");
  else notes.push("Low step count.");

  if ((latest.workout_session_count ?? 0) > 0) notes.push("Workout recorded.");
  if ((latest.energy_score ?? 0) >= 80) notes.push("Energy score looks good.");
  if ((latest.sleep_total_minutes ?? 0) >= 420) notes.push("Sleep duration looks supportive.");

  return {
    status: "ok",
    daily_brief: {
      snapshot_date: latest.snapshot_date,
      steps: latest.steps,
      distance_km: round((latest.distance_meters ?? 0) / 1000),
      active_calories: round(latest.active_calories),
      average_heart_rate: round(latest.average_heart_rate),
      energy_score: round(latest.energy_score),
      sleep_duration: formatMinutes(latest.sleep_total_minutes),
      workout_sessions: latest.workout_session_count,
      workout_duration: formatMinutes(latest.workout_total_duration_minutes),
      coach_note: notes.join(" "),
    },
  };
}

function buildTrainingWindow(rows: any[], label: string) {
  const workoutDays = rows.filter((row) => Number(row.workout_session_count ?? 0) > 0).length;
  const workoutSessions = sum(rows, "workout_session_count");
  const workoutMinutes = sum(rows, "workout_total_duration_minutes");
  const avgSleep = average(rows, "sleep_total_minutes");
  const avgEnergy = average(rows, "energy_score");
  const avgHeartRate = average(rows, "average_heart_rate");
  const avgRestingHr = average(rows, "resting_heart_rate");

  let load = "Low";
  if (workoutMinutes >= 600 || workoutDays >= 5) load = "High";
  else if (workoutMinutes >= 240 || workoutDays >= 3) load = "Moderate";

  let recovery = "Unknown";
  if ((avgEnergy ?? 0) >= 80 || (avgSleep ?? 0) >= 420) recovery = "Good";
  else if ((avgEnergy ?? 0) >= 65 || (avgSleep ?? 0) >= 360) recovery = "Mixed";
  else if (avgEnergy !== null || avgSleep !== null) recovery = "Strained";

  let note = "Insufficient recovery data.";
  if (load === "High" && recovery === "Good") {
    note = "Productive load: high training volume with supportive recovery signals.";
  } else if (load === "High") {
    note = "High load: watch recovery, sleep, hydration, and avoid unnecessary extra intensity.";
  } else if (load === "Moderate" && recovery === "Good") {
    note = "Balanced training load with supportive recovery.";
  }

  return {
    period: label,
    workout_days: workoutDays,
    workout_sessions: Math.round(workoutSessions),
    workout_duration: formatMinutes(workoutMinutes),
    average_sleep: formatMinutes(avgSleep),
    average_energy_score: round(avgEnergy),
    average_heart_rate: round(avgHeartRate),
    average_resting_heart_rate: round(avgRestingHr),
    load,
    recovery,
    vitalis_note: note,
  };
}

async function getTrainingRecovery() {
  const rows = await getRecentRows(30);

  if (rows.length === 0) {
    return { status: "empty", latest_health_date: null, training_recovery: null };
  }

  return {
    status: "ok",
    latest_health_date: rows[0].snapshot_date,
    training_recovery: [
      buildTrainingWindow(rows.slice(0, 7), "Last 7 days"),
      buildTrainingWindow(rows.slice(0, 14), "Last 14 days"),
      buildTrainingWindow(rows.slice(0, 30), "Last 30 days"),
    ],
  };
}

async function getLast30TrainingRecovery() {
  const rows = await getRecentRows(30);

  if (rows.length === 0) {
    return { status: "empty", latest_health_date: null, last_30_training_recovery: null };
  }

  return {
    status: "ok",
    latest_health_date: rows[0].snapshot_date,
    last_30_training_recovery: buildTrainingWindow(rows.slice(0, 30), "Last 30 days"),
  };
}

function messageResponse(lines: string[]) {
  return jsonResponse({
    message: lines.join("\n"),
  });
}

Deno.serve(async (request) => {
  if (request.method === "OPTIONS") {
    return jsonResponse({ status: "ok" });
  }

  try {
    const path = new URL(request.url).pathname.split("/").filter(Boolean).pop();

    if (request.method === "POST" && path === "upload-snapshot") {
      const payload = await request.json();
      const snapshot = normalizeSnapshot(payload);
      const rows = await supabaseUpsertSnapshot(snapshot);

      return jsonResponse({
        status: "ok",
        message: "Snapshot uploaded.",
        snapshot_date: snapshot.snapshot_date,
        rows,
      });
    }

    if (request.method !== "GET") {
      return jsonResponse(
        {
          status: "error",
          message: "Method not allowed.",
        },
        405
      );
    }

    if (path === "range") {
      return jsonResponse(await getRange());
    }

    if (path === "range-message") {
      const result = await getRange();

      return messageResponse([
        `first_date: ${result.first_date}`,
        `latest_date: ${result.latest_date}`,
        `total_snapshots: ${result.total_snapshots}`,
      ]);
    }

    if (path === "latest-summary") {
      return jsonResponse(await getLatestSummary());
    }

    if (path === "compare-periods-message") {
      const url = new URL(request.url);
      const periodA = url.searchParams.get("period_a");
      const periodB = url.searchParams.get("period_b");

      if (!periodA || !periodB) {
        return messageResponse([
          "error: missing period_a or period_b",
          "examples:",
          "/compare-periods-message?period_a=2026-08-08&period_b=2026-08-09",
          "/compare-periods-message?period_a=2026-07&period_b=2026-08",
          "/compare-periods-message?period_a=2025&period_b=2026",
          "/compare-periods-message?period_a=2026-08-01..2026-08-07&period_b=2026-08-08..2026-08-14",
        ]);
      }

      const result = await comparePeriods(periodA, periodB);

      return messageResponse(compareMessageLines(result.summaryA, result.summaryB));
    }


    if (path === "snapshot-message") {
      const date = new URL(request.url).searchParams.get("date");

      if (!date) {
        return messageResponse([
          "error: missing date parameter",
          "example: /snapshot-message?date=2026-08-08",
        ]);
      }

      const result = await getSnapshotByDate(date);

      if (result.status !== "ok" || !result.snapshot) {
        return messageResponse([
          `No snapshot found for date: ${date}`,
        ]);
      }

      return messageResponse(snapshotMessageLines(result.snapshot));
    }

    if (path === "latest-summary-message") {
      const result = await getLatestSummary();
      const snapshot = result.latest_summary;

      if (!snapshot) {
        return jsonResponse({
          message: "No latest health summary available.",
        });
      }

      return messageResponse([
        `snapshot_date: ${snapshot.snapshot_date}`,
        `steps: ${snapshot.steps}`,
        `distance_meters: ${snapshot.distance_meters}`,
        `active_calories: ${snapshot.active_calories}`,
        `average_heart_rate: ${snapshot.average_heart_rate}`,
        `minimum_heart_rate: ${snapshot.minimum_heart_rate}`,
        `maximum_heart_rate: ${snapshot.maximum_heart_rate}`,
        `resting_heart_rate: ${snapshot.resting_heart_rate}`,
        `sleep_total_minutes: ${snapshot.sleep_total_minutes}`,
        `sleep_score: ${snapshot.sleep_score}`,
        `energy_score: ${snapshot.energy_score}`,
        `energy_sleep_score: ${snapshot.energy_sleep_score}`,
        `energy_activity_score: ${snapshot.energy_activity_score}`,
        `workout_session_count: ${snapshot.workout_session_count}`,
		`workout_total_duration_minutes: ${snapshot.workout_total_duration_minutes}`,
		`vitalis_readiness_score: ${snapshot.vitalis_readiness_score}`,
		`vitalis_sleep_quality_score: ${snapshot.vitalis_sleep_quality_score}`,
		`vitalis_recovery_score: ${snapshot.vitalis_recovery_score}`,
		`vitalis_training_load_score: ${snapshot.vitalis_training_load_score}`,
		`vitalis_coach_note: ${snapshot.vitalis_coach_note}`,
		`source: ${snapshot.source}`,
      ]);
    }

    if (path === "daily-brief") {
      return jsonResponse(await getDailyBrief());
    }

    if (path === "daily-brief-message") {
      const result = await getDailyBrief();
      const brief = result.daily_brief;

      if (!brief) {
        return jsonResponse({
          message: "No daily brief available.",
        });
      }

      return messageResponse([
        `snapshot_date: ${brief.snapshot_date}`,
        `steps: ${brief.steps}`,
        `distance_km: ${brief.distance_km}`,
        `active_calories: ${brief.active_calories}`,
        `average_heart_rate: ${brief.average_heart_rate}`,
        `energy_score: ${brief.energy_score}`,
        `sleep_duration: ${brief.sleep_duration}`,
        `workout_sessions: ${brief.workout_sessions}`,
        `workout_duration: ${brief.workout_duration}`,
        `coach_note: ${brief.coach_note}`,
      ]);
    }

    if (path === "training-recovery") {
      return jsonResponse(await getTrainingRecovery());
    }

    if (path === "last-30-training-recovery") {
      return jsonResponse(await getLast30TrainingRecovery());
    }

    if (path === "last-30-training-message") {
      const result = await getLast30TrainingRecovery();

      if (result.status !== "ok" || !result.last_30_training_recovery) {
        return jsonResponse({
          message: "No last 30 days training recovery data available.",
        });
      }

      const summary = result.last_30_training_recovery;

      return messageResponse([
        `period: ${summary.period}`,
        `workout_days: ${summary.workout_days}`,
        `workout_sessions: ${summary.workout_sessions}`,
        `workout_duration: ${summary.workout_duration}`,
        `average_sleep: ${summary.average_sleep}`,
        `average_energy_score: ${summary.average_energy_score}`,
        `average_heart_rate: ${summary.average_heart_rate}`,
        `average_resting_heart_rate: ${summary.average_resting_heart_rate}`,
        `load: ${summary.load}`,
        `recovery: ${summary.recovery}`,
        `vitalis_note: ${summary.vitalis_note}`,
      ]);
    }

    if (path === "last-30-training-flat") {
      const result = await getLast30TrainingRecovery();

      if (result.status !== "ok" || !result.last_30_training_recovery) {
        return jsonResponse({
          status: "empty",
          latest_health_date: result.latest_health_date ?? null,
          period: "Last 30 days",
          workout_days: null,
          workout_sessions: null,
          workout_duration: null,
          average_sleep: null,
          average_energy_score: null,
          average_heart_rate: null,
          average_resting_heart_rate: null,
          load: null,
          recovery: null,
          vitalis_note: "No last 30 days training recovery data available.",
        });
      }

      const summary = result.last_30_training_recovery;

      return jsonResponse({
        status: "ok",
        latest_health_date: result.latest_health_date,
        period: summary.period,
        workout_days: summary.workout_days,
        workout_sessions: summary.workout_sessions,
        workout_duration: summary.workout_duration,
        average_sleep: summary.average_sleep,
        average_energy_score: summary.average_energy_score,
        average_heart_rate: summary.average_heart_rate,
        average_resting_heart_rate: summary.average_resting_heart_rate,
        load: summary.load,
        recovery: summary.recovery,
        vitalis_note: summary.vitalis_note,
      });
    }

    if (path === "last-30-training-text") {
      const result = await getLast30TrainingRecovery();

      if (result.status !== "ok" || !result.last_30_training_recovery) {
        return new Response("No last 30 days training recovery data available.", {
          headers: {
            "Content-Type": "text/plain; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
          },
        });
      }

      const summary = result.last_30_training_recovery;

      return new Response(
        [
          `status: ok`,
          `latest_health_date: ${result.latest_health_date}`,
          `period: ${summary.period}`,
          `workout_days: ${summary.workout_days}`,
          `workout_sessions: ${summary.workout_sessions}`,
          `workout_duration: ${summary.workout_duration}`,
          `average_sleep: ${summary.average_sleep}`,
          `average_energy_score: ${summary.average_energy_score}`,
          `average_heart_rate: ${summary.average_heart_rate}`,
          `average_resting_heart_rate: ${summary.average_resting_heart_rate}`,
          `load: ${summary.load}`,
          `recovery: ${summary.recovery}`,
          `vitalis_note: ${summary.vitalis_note}`,
        ].join("\n"),
        {
          headers: {
            "Content-Type": "text/plain; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
          },
        }
      );
    }

    return jsonResponse({
      status: "ok",
      service: "Vitalis API",
      endpoints: [
        "/range",
        "/latest-summary",
        "/daily-brief",
        "/training-recovery",
        "/last-30-training-recovery",
        "/range-message",
		"/compare-periods-message?period_a=YYYY-MM-DD&period_b=YYYY-MM-DD",
		"/snapshot-message?date=YYYY-MM-DD",
        "/latest-summary-message",
        "/daily-brief-message",
        "/last-30-training-message",
        "/last-30-training-flat",
        "/last-30-training-text",
        "/upload-snapshot",
      ],
    });
  } catch (error) {
    return jsonResponse(
      {
        status: "error",
        message: error instanceof Error ? error.message : String(error),
      },
      500
    );
  }
});
