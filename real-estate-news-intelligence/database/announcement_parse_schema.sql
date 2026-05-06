CREATE TABLE IF NOT EXISTS parsed_announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    announcement_title TEXT,
    announcement_types TEXT,
    companies TEXT,
    risk_keywords TEXT,
    amounts TEXT,
    revenue TEXT,
    net_profit TEXT,
    interest_bearing_debt TEXT,
    cash_and_equivalents TEXT,
    risks TEXT,
    file_path TEXT,
    source_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
