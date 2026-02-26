-- sql/schema.sql
-- SQLite schema for Project Echo local cache
-- This file creates the necessary tables for caching data from HosXP

-- Metadata table for tracking sync operations
CREATE TABLE IF NOT EXISTS sync_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_time   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    table_name  TEXT NOT NULL,
    row_count   INTEGER DEFAULT 0,
    status      TEXT DEFAULT 'success',
    message     TEXT
);

-- Example: cached query results
-- Tables are typically auto-created by pandas to_sql()
-- This schema is for reference only
