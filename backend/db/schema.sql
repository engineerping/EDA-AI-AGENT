CREATE TABLE IF NOT EXISTS components (
    lib_id       TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    keywords     TEXT NOT NULL DEFAULT '',
    category     TEXT NOT NULL DEFAULT '',
    pin_count    INTEGER NOT NULL DEFAULT 0,
    datasheet_url TEXT NOT NULL DEFAULT '',
    pins_json    TEXT NOT NULL DEFAULT '[]'
);

CREATE VIRTUAL TABLE IF NOT EXISTS components_fts
    USING fts5(lib_id, name, description, keywords, content='components', content_rowid='rowid');

CREATE TRIGGER IF NOT EXISTS components_ai AFTER INSERT ON components BEGIN
    INSERT INTO components_fts(rowid, lib_id, name, description, keywords)
    VALUES (new.rowid, new.lib_id, new.name, new.description, new.keywords);
END;
