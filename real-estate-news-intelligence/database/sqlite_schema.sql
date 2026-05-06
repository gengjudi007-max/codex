CREATE TABLE IF NOT EXISTS raw_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT,
    source_type TEXT,
    source_url TEXT UNIQUE,
    title TEXT,
    publish_time TEXT,
    fetch_time TEXT DEFAULT CURRENT_TIMESTAMP,
    file_url TEXT,
    file_hash TEXT,
    raw_text TEXT,
    raw_html TEXT,
    status TEXT DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS parsed_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_document_id INTEGER,
    document_type TEXT,
    title TEXT,
    publish_time TEXT,
    region TEXT,
    company_name TEXT,
    stock_code TEXT,
    issuing_authority TEXT,
    summary TEXT,
    keywords TEXT,
    risk_keywords TEXT,
    amounts TEXT,
    dates TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(raw_document_id) REFERENCES raw_documents(id)
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_title TEXT,
    topic_type TEXT,
    trigger_event TEXT,
    related_companies TEXT,
    related_regions TEXT,
    news_value_score REAL,
    urgency_score REAL,
    exclusivity_score REAL,
    data_support_score REAL,
    risk_score REAL,
    total_score REAL,
    topic_status TEXT DEFAULT 'candidate',
    summary TEXT,
    suggested_angle TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER,
    material_type TEXT,
    source_name TEXT,
    source_url TEXT,
    content TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(topic_id) REFERENCES topics(id)
);

CREATE TABLE IF NOT EXISTS fact_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER,
    check_item TEXT,
    check_result TEXT,
    source_reference TEXT,
    checked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(topic_id) REFERENCES topics(id)
);
