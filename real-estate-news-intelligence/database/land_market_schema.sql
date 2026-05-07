CREATE TABLE IF NOT EXISTS land_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    district TEXT,
    parcel_name TEXT,
    land_use TEXT,
    land_area REAL,
    construction_area REAL,
    starting_price REAL,
    transaction_price REAL,
    premium_rate REAL,
    floor_price REAL,
    winner_company TEXT,
    winner_company_type TEXT,
    is_chengtou INTEGER,
    actual_controller TEXT,
    transaction_date TEXT,
    announcement_date TEXT,
    development_status TEXT,
    idle_status TEXT,
    source_name TEXT,
    source_url TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS land_daily_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    statistic_date TEXT,
    transaction_count INTEGER,
    transaction_amount REAL,
    average_premium_rate REAL,
    chengtou_ratio REAL,
    private_developer_ratio REAL,
    state_owned_ratio REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
