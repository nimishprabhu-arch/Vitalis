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
      "Access-Control-Allow-Methods": "GET, OPTIONS",
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

function round(value: unknown, digits = 2) {
  if (value === null || value === undefined || value === "") return null;
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) return null;
  return Number(numberValue.toFixed(digits));
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

async function getLatestRow() {
  const rows = await supabaseGet(`${TABLE}?select=*&order=snapshot_date.desc&limit=1`);
  return rows?.[0] ?? null;
}

async function getRecentRows(days: number) {
  const rows = await supabaseGet(`${TABLE}?select=*&order=snapshot_date.desc&limit=${days}`);
  return Array.isArray(rows) ? rows : [];
}

async function getRange() {
  const firstRows = await supabaseGet(`${TABLE}?select=snapshot_date&order=snapshot_date.asc&limit=1`);
  const latestRows = await supabaseGet(`${TABLE}?select=snapshot_date&order=snapshot_date.desc&limit=1`);
  const countRows = await supabaseGet(`${TABLE}?select=snapshot_date`);

  return {
    status: "ok",
    first_date: firstRows?.[0]?.snapshot_date ?? null,
    latest_date: latestRows?.[0]?.snapshot_date ?? null,
    total_snapshots: Array.isArray(countRows) ? countRows.length : null,
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
          workout_session_count: row.workout_session_count,
          workout_total_duration_minutes: row.workout_total_duration_minutes,
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
    return { status: "empty", last_30_training_recovery: null };
  }

  return {
    status: "ok",
    latest_health_date: rows[0].snapshot_date,
    last_30_training_recovery: buildTrainingWindow(rows.slice(0, 30), "Last 30 days"),
  };
}

Deno.serve(async (request) => {
  if (request.method === "OPTIONS") {
    return jsonResponse({ status: "ok" });
  }

  try {
    const path = new URL(request.url).pathname.split("/").filter(Boolean).pop();

    if (path === "range") return jsonResponse(await getRange());
    if (path === "latest-summary") return jsonResponse(await getLatestSummary());
    if (path === "daily-brief") return jsonResponse(await getDailyBrief());
    if (path === "training-recovery") return jsonResponse(await getTrainingRecovery());
    if (path === "last-30-training-recovery") return jsonResponse(await getLast30TrainingRecovery());
	if (path === "last-30-training-message") {
  const result = await getLast30TrainingRecovery();

  if (result.status !== "ok" || !result.last_30_training_recovery) {
    return jsonResponse({
      message: "No last 30 days training recovery data available."
    });
  }

  const summary = result.last_30_training_recovery;

  return jsonResponse({
    message: [
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
      `vitalis_note: ${summary.vitalis_note}`
    ].join("\n")
  });
}
	
	if (path === "last-30-training-message") {
  const result = await getLast30TrainingRecovery();

  if (result.status !== "ok" || !result.last_30_training_recovery) {
    return jsonResponse({
      message: "No last 30 days training recovery data available."
    });
  }

  const summary = result.last_30_training_recovery;

  return jsonResponse({
    message: [
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
      `vitalis_note: ${summary.vitalis_note}`
    ].join("\n")
  });
}
	
	if (path === "last-30-training-text") {
  const result = await getLast30TrainingRecovery();

  if (result.status !== "ok" || !result.last_30_training_recovery) {
    return new Response("No last 30 days training recovery data available.", {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Access-Control-Allow-Origin": "*"
      }
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
      `vitalis_note: ${summary.vitalis_note}`
    ].join("\n"),
    {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Access-Control-Allow-Origin": "*"
      }
    }
  );
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
    return jsonResponse({
      status: "ok",
      service: "Vitalis API",
      endpoints: [
        "/range",
        "/latest-summary",
        "/daily-brief",
        "/training-recovery",
        "/last-30-training-recovery",
"/last-30-training-message",
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