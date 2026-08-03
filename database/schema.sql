CREATE TABLE IF NOT EXISTS daily_health_snapshots (
    snapshot_date TEXT PRIMARY KEY,
    saved_at TEXT NOT NULL,

    steps INTEGER,
    distance_meters REAL,
    active_calories REAL,
    floors REAL,

    average_heart_rate REAL,
    minimum_heart_rate INTEGER,
    maximum_heart_rate INTEGER,
    resting_heart_rate INTEGER,

    sleep_total_minutes INTEGER,
    deep_sleep_minutes INTEGER,
    rem_sleep_minutes INTEGER,
    light_sleep_minutes INTEGER,
    awake_minutes INTEGER,
    sleep_session_count INTEGER,

    workout_session_count INTEGER,
    workout_total_duration_minutes INTEGER,

    source_file TEXT,
    imported_at TEXT NOT NULL
);