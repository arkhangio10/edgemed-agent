CREATE TABLE IF NOT EXISTS queue_items (
    note_id         TEXT PRIMARY KEY,
    idempotency_key TEXT UNIQUE NOT NULL,
    mode            TEXT NOT NULL CHECK(mode IN ('demo','prod')),
    ciphertext      BLOB NOT NULL,
    status          TEXT NOT NULL DEFAULT 'queued'
                    CHECK(status IN ('queued','syncing','synced','failed')),
    fail_reason     TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    retry_count     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sync_attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id         TEXT NOT NULL REFERENCES queue_items(note_id),
    attempted_at    TEXT NOT NULL DEFAULT (datetime('now')),
    success         INTEGER NOT NULL,
    response_code   INTEGER,
    error_message   TEXT,
    duration_ms     INTEGER
);

CREATE INDEX IF NOT EXISTS idx_queue_status ON queue_items(status);
CREATE INDEX IF NOT EXISTS idx_queue_created ON queue_items(created_at);
