-- Персональные настройки генерации для каждого пользователя.
CREATE TABLE IF NOT EXISTS user_settings (
    user_id    INTEGER PRIMARY KEY REFERENCES users(user_id),
    aspect     TEXT    NOT NULL DEFAULT 'square',   -- square|landscape|portrait|wide|tall|auto|custom
    custom_w   INTEGER,
    custom_h   INTEGER,
    quality    TEXT    NOT NULL DEFAULT 'high',      -- low|medium|high
    model      TEXT    NOT NULL DEFAULT 'gpt-image-2',
    fidelity   TEXT    NOT NULL DEFAULT 'low',        -- low|high (input_fidelity для референсов)
    updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
