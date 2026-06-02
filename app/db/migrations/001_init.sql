CREATE TABLE IF NOT EXISTS users (
    user_id    INTEGER PRIMARY KEY,
    username   TEXT,
    first_name TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS image_generations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(user_id),
    prompt     TEXT    NOT NULL,
    model      TEXT    NOT NULL,
    size       TEXT    NOT NULL,
    quality    TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'ok',   -- ok | error
    error      TEXT,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_generations_user ON image_generations(user_id);
