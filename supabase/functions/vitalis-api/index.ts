const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: {
      ...corsHeaders,
      "Content-Type": "application/json",
    },
  });
}

function getSupabaseConfig() {
  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error("Missing Supabase environment variables.");
  }

  return { supabaseUrl, serviceRoleKey };
}

async function querySupabase(path: string) {
  const { supabaseUrl, serviceRoleKey } = getSupabaseConfig();

  const response = await fetch(`${supabaseUrl}/rest/v1/${path}`, {
    headers: {
      apikey: serviceRoleKey,
      Authorization: `Bearer ${serviceRoleKey}`,
    },
  });

  const data = await response.json();

  return {
    ok: response.ok,
    status: response.status,
    data,
  };
}

async function countSnapshots() {
  const { supabaseUrl, serviceRoleKey } = getSupabaseConfig();

  const response = await fetch(
    `${supabaseUrl}/rest/v1/health_snapshots?select=snapshot_date&limit=1`,
    {
      headers: {
        apikey: serviceRoleKey,
        Authorization: `Bearer ${serviceRoleKey}`,
        Prefer: "count=exact",
      },
    },
  );

  if (!response.ok) {
    const data = await response.json();
    return {
      ok: false,
      status: response.status,
      count: null,
      data,
    };
  }

  const contentRange = response.headers.get("content-range");
  const countText = contentRange?.split("/")?.[1] ?? null;
  const count = countText ? Number(countText) : null;

  return {
    ok: true,
    status: response.status,
    count,
    data: null,
  };
}

function buildLatestSummary(snapshot: Record<string, unknown> | null) {
  if (!snapshot) {
    return null;
  }

  return {
    snapshot_date: snapshot.snapshot_date ?? null,
    saved_at: snapshot.saved_at ?? null,

    steps: snapshot.steps ?? null,
    distance_meters: snapshot.distance_meters ?? null,
    active_calories: snapshot.active_calories ?? null,
    floors: snapshot.floors ?? null,

    average_heart_rate: snapshot.average_heart_rate ?? null,
    minimum_heart_rate: snapshot.minimum_heart_rate ?? null,
    maximum_heart_rate: snapshot.maximum_heart_rate ?? null,
    resting_heart_rate: snapshot.resting_heart_rate ?? null,

    sleep_total_minutes: snapshot.sleep_total_minutes ?? null,
    deep_sleep_minutes: snapshot.deep_sleep_minutes ?? null,
    rem_sleep_minutes: snapshot.rem_sleep_minutes ?? null,
    light_sleep_minutes: snapshot.light_sleep_minutes ?? null,
    awake_minutes: snapshot.awake_minutes ?? null,
    sleep_session_count: snapshot.sleep_session_count ?? null,

    sleep_score: snapshot.sleep_score ?? null,
    sleep_efficiency: snapshot.sleep_efficiency ?? null,
    physical_recovery: snapshot.physical_recovery ?? null,
    mental_recovery: snapshot.mental_recovery ?? null,

    energy_score: snapshot.energy_score ?? null,
    energy_sleep_score: snapshot.energy_sleep_score ?? null,
    energy_activity_score: snapshot.energy_activity_score ?? null,

    workout_session_count: snapshot.workout_session_count ?? null,
    workout_total_duration_minutes: snapshot.workout_total_duration_minutes ?? null,

    source: snapshot.source ?? null,
  };
}

Deno.serve(async (request) => {
  if (request.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const url = new URL(request.url);
    const route = url.pathname.split("/").filter(Boolean).pop();

    if (route === "latest") {
      const result = await querySupabase(
        "health_snapshots?select=*&order=snapshot_date.desc&limit=1",
      );

      if (!result.ok) {
        return jsonResponse({ error: "Supabase query failed", details: result.data }, result.status);
      }

      return jsonResponse({
        status: "ok",
        snapshot: result.data[0] ?? null,
      });
    }

    if (route === "latest-summary") {
      const result = await querySupabase(
        "health_snapshots?select=*&order=snapshot_date.desc&limit=1",
      );

      if (!result.ok) {
        return jsonResponse({ error: "Supabase query failed", details: result.data }, result.status);
      }

      return jsonResponse({
        status: "ok",
        latest_summary: buildLatestSummary(result.data[0] ?? null),
      });
    }

    if (route === "range") {
      const earliest = await querySupabase(
        "health_snapshots?select=snapshot_date&order=snapshot_date.asc&limit=1",
      );

      const latest = await querySupabase(
        "health_snapshots?select=snapshot_date&order=snapshot_date.desc&limit=1",
      );

      const count = await countSnapshots();

      if (!earliest.ok || !latest.ok || !count.ok) {
        return jsonResponse({ error: "Supabase query failed" }, 500);
      }

      return jsonResponse({
        status: "ok",
        first_date: earliest.data[0]?.snapshot_date ?? null,
        latest_date: latest.data[0]?.snapshot_date ?? null,
        total_snapshots: count.count,
      });
    }

    return jsonResponse({
      status: "ok",
      service: "Vitalis API",
      routes: ["/latest", "/latest-summary", "/range"],
    });
  } catch (error) {
    return jsonResponse(
      {
        status: "error",
        message: error instanceof Error ? error.message : String(error),
      },
      500,
    );
  }
});