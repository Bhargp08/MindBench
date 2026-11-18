-- MindBench SQLite schema (MB-14). Foreign keys must be enabled per connection (db.connect does this).

CREATE TABLE IF NOT EXISTS participants (
    participant_code TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS sessions (
    participant_code TEXT NOT NULL REFERENCES participants (participant_code),
    session_number INTEGER NOT NULL CHECK (session_number >= 1),
    is_pilot INTEGER NOT NULL CHECK (is_pilot IN (0, 1)),   -- 1 for the 10 pilot sessions (excluded from confirmatory analysis)
    excluded_reason TEXT,                                  -- NULL unless a preregistered exclusion rule (MB-15) or a manual note sets it
    timestamp TEXT,
    timezone TEXT,
    user_agent TEXT,
    screen_width INTEGER,
    screen_height INTEGER,
    jspsych_version TEXT,
    task_order TEXT,                                       -- JSON array of task names in the order run
    viewing_distance_cm REAL,                              -- instructed distance, not measured
    refresh_hz REAL,
    refresh_plausible INTEGER,
    total_task_ms REAL,
    source_filename TEXT,
    PRIMARY KEY (participant_code, session_number)
);

CREATE TABLE IF NOT EXISTS questionnaire (
    participant_code TEXT NOT NULL,
    session_number INTEGER NOT NULL,
    hours_slept REAL,
    bed_time TEXT,
    wake_time TEXT,
    kss INTEGER,
    caffeine INTEGER,
    device TEXT,
    PRIMARY KEY (participant_code, session_number),
    FOREIGN KEY (participant_code, session_number) REFERENCES sessions (participant_code, session_number)
);

CREATE TABLE IF NOT EXISTS trials (
    participant_code TEXT NOT NULL,
    session_number INTEGER NOT NULL,
    trial_index INTEGER NOT NULL,                          -- jsPsych trial_index within the session
    task TEXT,                                             -- NULL for rows without a task tag (consent, survey screens)
    practice INTEGER,                                      -- 1 practice, 0 scored, NULL for untagged rows (fixation, cues)
    rt REAL,
    response TEXT,
    correct INTEGER,
    data_json TEXT NOT NULL,                               -- the full row minus session-level properties
    PRIMARY KEY (participant_code, session_number, trial_index),
    FOREIGN KEY (participant_code, session_number) REFERENCES sessions (participant_code, session_number)
);

CREATE INDEX IF NOT EXISTS idx_trials_task ON trials (task);
