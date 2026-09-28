-- Tsync PostgreSQL / SQLite Initial Schema DDL

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(128) NOT NULL,
    source_channel VARCHAR(128) NOT NULL,
    text TEXT NOT NULL,
    cleaned_text TEXT NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    category VARCHAR(64) DEFAULT 'uncategorized',
    importance_score DOUBLE PRECISION DEFAULT 0.0,
    is_selected BOOLEAN DEFAULT FALSE,
    headline VARCHAR(256),
    summary TEXT,
    why_it_matters TEXT,
    incident_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_source_external UNIQUE (source_channel, external_id)
);

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(256) NOT NULL,
    category VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'NEW',
    severity VARCHAR(32) DEFAULT 'LOW',
    importance_score DOUBLE PRECISION DEFAULT 0.0,
    confidence_score DOUBLE PRECISION DEFAULT 0.5,
    summary TEXT DEFAULT '',
    why_it_matters TEXT DEFAULT '',
    sources_json TEXT DEFAULT '[]',
    contradictions_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS incident_timeline (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    content TEXT NOT NULL,
    source_channel VARCHAR(128) DEFAULT '',
    importance_score DOUBLE PRECISION DEFAULT 0.0,
    is_major_event BOOLEAN DEFAULT FALSE,
    message_id INTEGER
);

CREATE TABLE IF NOT EXISTS incident_claims (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    message_id INTEGER,
    statement TEXT NOT NULL,
    source_name VARCHAR(128) DEFAULT '',
    confidence DOUBLE PRECISION DEFAULT 0.5,
    is_disputed BOOLEAN DEFAULT FALSE,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS incident_entities (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    entity_type VARCHAR(64) DEFAULT 'other',
    normalized_name VARCHAR(128) NOT NULL,
    relevance_score DOUBLE PRECISION DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    username_or_id VARCHAR(128) UNIQUE NOT NULL,
    title VARCHAR(128) DEFAULT '',
    source_type VARCHAR(32) DEFAULT 'telegram',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_polled_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS notification_audit (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    recipient VARCHAR(128) NOT NULL,
    channel VARCHAR(32) NOT NULL,
    message_payload TEXT NOT NULL,
    status VARCHAR(32) DEFAULT 'sent',
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_pub ON messages(published_at);
CREATE INDEX IF NOT EXISTS idx_messages_cat ON messages(category);
CREATE INDEX IF NOT EXISTS idx_messages_score ON messages(importance_score);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_cat ON incidents(category);
CREATE INDEX IF NOT EXISTS idx_incidents_updated ON incidents(updated_at);
