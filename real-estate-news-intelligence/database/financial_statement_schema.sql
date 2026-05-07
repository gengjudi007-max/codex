CREATE TABLE IF NOT EXISTS financial_statement_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    report_period TEXT,
    table_type TEXT,
    page_number INTEGER,
    table_index INTEGER,
    raw_json TEXT,
    source_file TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS financial_statement_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    report_period TEXT,
    metric_name TEXT,
    metric_value TEXT,
    metric_unit TEXT,
    table_type TEXT,
    source_file TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
