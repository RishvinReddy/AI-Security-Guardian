-- AI Security Guardian - Database Schema v2

-- 1. Assets
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID,
    asset_value VARCHAR(255) NOT NULL, -- e.g., 'example.com'
    asset_type VARCHAR(50) NOT NULL,   -- e.g., 'domain', 'ip', 'github_repo'
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, asset_value)
);

-- 2. Executions (Tracks each workflow run)
CREATE TABLE IF NOT EXISTS executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    status VARCHAR(50) NOT NULL, -- e.g., 'running', 'completed', 'failed'
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    scanners_success_count INTEGER,
    scanners_failed_count INTEGER
);

-- 3. Raw Scanner Results
CREATE TABLE IF NOT EXISTS raw_scanner_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    scanner_name VARCHAR(100) NOT NULL,
    raw_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Findings (Normalized security issues)
CREATE TABLE IF NOT EXISTS findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    scanner_name VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL, -- critical, high, medium, low, informational
    finding_title VARCHAR(255) NOT NULL,
    finding_details JSONB,
    status VARCHAR(50) DEFAULT 'open',
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Risk Scores
CREATE TABLE IF NOT EXISTS risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    score INTEGER NOT NULL, -- 0-100
    factors JSONB NOT NULL, -- Explanation of what contributed to the score
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. AI Reports
CREATE TABLE IF NOT EXISTS ai_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    summary TEXT,
    priority VARCHAR(50),
    business_impact TEXT,
    technical_analysis TEXT,
    recommendations JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Additional Table for Threat Intel Caching
CREATE TABLE IF NOT EXISTS threat_intel_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    indicator_value VARCHAR(255) NOT NULL, -- e.g., '1.1.1.1'
    indicator_type VARCHAR(50) NOT NULL,   -- e.g., 'ip', 'domain', 'hash'
    source VARCHAR(100) NOT NULL,          -- e.g., 'virustotal'
    report_data JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    UNIQUE(indicator_value, source)
);
