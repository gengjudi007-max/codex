CREATE TABLE raw_documents (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT,
    source_type TEXT,
    source_url TEXT,
    title TEXT,
    publish_time TIMESTAMP,
    fetch_time TIMESTAMP DEFAULT NOW(),
    file_url TEXT,
    file_hash TEXT,
    raw_text TEXT,
    raw_html TEXT,
    status TEXT DEFAULT 'new'
);

CREATE TABLE companies (
    id BIGSERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    stock_code TEXT,
    exchange TEXT,
    company_type TEXT,
    actual_controller TEXT,
    region TEXT,
    business_segments TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE company_announcements (
    id BIGSERIAL PRIMARY KEY,
    company_name TEXT,
    stock_code TEXT,
    exchange TEXT,
    announcement_title TEXT,
    announcement_type TEXT,
    publish_time TIMESTAMP,
    source_url TEXT,
    file_url TEXT,
    summary TEXT,
    keywords TEXT[],
    risk_level TEXT,
    raw_document_id BIGINT REFERENCES raw_documents(id)
);

CREATE TABLE policies (
    id BIGSERIAL PRIMARY KEY,
    title TEXT,
    issuing_authority TEXT,
    region TEXT,
    policy_level TEXT,
    publish_time TIMESTAMP,
    policy_type TEXT,
    key_terms TEXT[],
    summary TEXT,
    policy_signal TEXT,
    strength_score NUMERIC,
    source_url TEXT,
    raw_document_id BIGINT REFERENCES raw_documents(id)
);

CREATE TABLE land_transactions (
    id BIGSERIAL PRIMARY KEY,
    city TEXT,
    district TEXT,
    parcel_name TEXT,
    land_use TEXT,
    land_area NUMERIC,
    construction_area NUMERIC,
    transaction_price NUMERIC,
    starting_price NUMERIC,
    premium_rate NUMERIC,
    floor_price NUMERIC,
    winner_company TEXT,
    winner_company_type TEXT,
    is_chengtou BOOLEAN,
    announcement_date DATE,
    transaction_date DATE,
    development_status TEXT,
    source_url TEXT,
    raw_document_id BIGINT REFERENCES raw_documents(id)
);

CREATE TABLE real_estate_market_data (
    id BIGSERIAL PRIMARY KEY,
    city TEXT,
    data_date DATE,
    new_home_transaction_area NUMERIC,
    secondhand_transaction_area NUMERIC,
    inventory_area NUMERIC,
    de_inventory_months NUMERIC,
    average_price NUMERIC,
    source_name TEXT,
    source_url TEXT
);

CREATE TABLE financial_indicators (
    id BIGSERIAL PRIMARY KEY,
    company_name TEXT,
    stock_code TEXT,
    report_period TEXT,
    contracted_sales_amount NUMERIC,
    contracted_sales_area NUMERIC,
    revenue NUMERIC,
    gross_margin NUMERIC,
    net_profit NUMERIC,
    attributable_net_profit NUMERIC,
    cash NUMERIC,
    interest_bearing_debt NUMERIC,
    net_gearing_ratio NUMERIC,
    source_name TEXT,
    source_url TEXT
);

CREATE TABLE topics (
    id BIGSERIAL PRIMARY KEY,
    topic_title TEXT,
    topic_type TEXT,
    trigger_event TEXT,
    related_companies TEXT[],
    related_regions TEXT[],
    news_value_score NUMERIC,
    urgency_score NUMERIC,
    exclusivity_score NUMERIC,
    data_support_score NUMERIC,
    risk_score NUMERIC,
    topic_status TEXT DEFAULT 'candidate',
    summary TEXT,
    suggested_angle TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE materials (
    id BIGSERIAL PRIMARY KEY,
    topic_id BIGINT REFERENCES topics(id),
    material_type TEXT,
    source_name TEXT,
    source_url TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE interview_plans (
    id BIGSERIAL PRIMARY KEY,
    topic_id BIGINT REFERENCES topics(id),
    interview_target TEXT,
    interview_questions TEXT,
    priority_level TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE drafts (
    id BIGSERIAL PRIMARY KEY,
    topic_id BIGINT REFERENCES topics(id),
    draft_title TEXT,
    draft_type TEXT,
    content TEXT,
    draft_status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fact_checks (
    id BIGSERIAL PRIMARY KEY,
    draft_id BIGINT REFERENCES drafts(id),
    check_item TEXT,
    check_result TEXT,
    source_reference TEXT,
    checked_at TIMESTAMP DEFAULT NOW()
);
