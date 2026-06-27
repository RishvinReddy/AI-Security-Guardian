-- AI Security Guardian - Database Schema v2

-- 3. Assets (CMDB)
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(255) UNIQUE NOT NULL,
    owner VARCHAR(100),
    environment VARCHAR(50) DEFAULT 'Production',
    criticality VARCHAR(50) DEFAULT 'Medium',
    business_unit VARCHAR(100),
    tags JSONB,
    scan_profile VARCHAR(50) DEFAULT 'Standard',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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
    cache_key VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    response JSONB NOT NULL,
    confidence NUMERIC(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ttl_seconds INTEGER,
    hit_count INTEGER DEFAULT 0,
    refresh_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE,
    error_count INTEGER DEFAULT 0,
    UNIQUE(cache_key, provider)
);

-- PHASE 2 TABLES

-- 8. Scanner Metadata
CREATE TABLE IF NOT EXISTS scanner_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    scanner_name VARCHAR(100) NOT NULL,
    version VARCHAR(50),
    configuration JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Workflow Runs (n8n execution context mapping)
CREATE TABLE IF NOT EXISTS workflow_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    n8n_execution_id VARCHAR(255) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50)
);

-- 10. Historical Changes (Deltas between scans)
CREATE TABLE IF NOT EXISTS historical_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    previous_execution_id UUID REFERENCES executions(id),
    new_ports INT[],
    closed_ports INT[],
    new_cves TEXT[],
    resolved_cves TEXT[],
    risk_delta INTEGER,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. Dashboard & Security Intelligence Metrics
CREATE TABLE IF NOT EXISTS dashboard_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    date DATE DEFAULT CURRENT_DATE,
    operational_metrics JSONB NOT NULL,
    security_metrics JSONB NOT NULL,
    executive_metrics JSONB NOT NULL,
    business_metrics JSONB NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. Trend Analysis
CREATE TABLE IF NOT EXISTS trend_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    date DATE DEFAULT CURRENT_DATE,
    risk_score NUMERIC(5,2),
    risk_delta NUMERIC(5,2),
    finding_velocity JSONB,
    resolution_rate NUMERIC(5,2),
    scanner_health JSONB,
    confidence NUMERIC(3,2),
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. Report History
CREATE TABLE IF NOT EXISTS report_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    report_type VARCHAR(50) NOT NULL, -- executive, technical, remediation
    format VARCHAR(20) NOT NULL,      -- markdown, json, html, pdf
    content TEXT NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PHASE 3 TABLES

-- 14. Change Events
CREATE TABLE IF NOT EXISTS change_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    change_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence NUMERIC(3,2),
    business_impact VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 15. Incidents
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID REFERENCES assets(id),
    priority VARCHAR(10) NOT NULL,
    state VARCHAR(20) DEFAULT 'NEW',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 16. Incident Findings (Many-to-Many)
CREATE TABLE IF NOT EXISTS incident_findings (
    incident_id UUID REFERENCES incidents(id),
    finding_hash VARCHAR(255) NOT NULL,
    PRIMARY KEY (incident_id, finding_hash)
);

-- 17. Tickets
CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    provider VARCHAR(50) NOT NULL,
    external_ticket_id VARCHAR(255) NOT NULL,
    state VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 18. Ticket History
CREATE TABLE IF NOT EXISTS ticket_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES tickets(id),
    action VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 19. Notification History
CREATE TABLE IF NOT EXISTS notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    channel VARCHAR(50) NOT NULL,
    recipient VARCHAR(100),
    status VARCHAR(50),
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 20. Approval History
CREATE TABLE IF NOT EXISTS approval_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    approver VARCHAR(100),
    decision VARCHAR(20),
    comments TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 21. Escalation History
CREATE TABLE IF NOT EXISTS escalation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id),
    escalated_from VARCHAR(100),
    escalated_to VARCHAR(100),
    reason TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 22. Cloud Findings
CREATE TABLE IF NOT EXISTS cloud_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    provider VARCHAR(50) NOT NULL,
    account_id VARCHAR(100),
    region VARCHAR(50),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    finding_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 23. Container Findings
CREATE TABLE IF NOT EXISTS container_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    scan_type VARCHAR(50) NOT NULL, -- image, fs, sbom
    image_name VARCHAR(255),
    finding_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- PHASE 4 TABLES

-- 24. Roles
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- 25. Permissions
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID REFERENCES roles(id),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    UNIQUE(role_id, resource, action)
);

-- 26. Users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    role_id UUID REFERENCES roles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 27. API Keys
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    api_key_hash VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 28. Plugins
CREATE TABLE IF NOT EXISTS plugins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20),
    category VARCHAR(50),
    enabled BOOLEAN DEFAULT true,
    timeout INTEGER DEFAULT 60,
    priority INTEGER DEFAULT 1
);

-- 29. Plugin Settings
CREATE TABLE IF NOT EXISTS plugin_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID REFERENCES plugins(id),
    key VARCHAR(100) NOT NULL,
    value JSONB,
    UNIQUE(plugin_id, key)
);

-- 30. Plugin Credentials
CREATE TABLE IF NOT EXISTS plugin_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID REFERENCES plugins(id),
    credential_name VARCHAR(100) NOT NULL,
    encrypted_value TEXT NOT NULL
);

-- 31. Plugin Logs
CREATE TABLE IF NOT EXISTS plugin_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plugin_id UUID REFERENCES plugins(id),
    execution_id UUID REFERENCES executions(id),
    status VARCHAR(50),
    message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 32. IaC Findings
CREATE TABLE IF NOT EXISTS iac_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    asset_id UUID REFERENCES assets(id),
    framework VARCHAR(50) NOT NULL,
    resource_type VARCHAR(100),
    resource_name VARCHAR(255),
    misconfiguration TEXT NOT NULL,
    severity VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 33. Platform Events (Event Bus)
CREATE TABLE IF NOT EXISTS platform_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    correlation_id UUID,
    tenant_id VARCHAR(50),
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 34. AI Metrics
CREATE TABLE IF NOT EXISTS ai_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id),
    model_used VARCHAR(50),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_cost NUMERIC(10,5),
    latency_ms INTEGER,
    success BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 35. Workflow Health Incidents (Platform Monitoring)
CREATE TABLE IF NOT EXISTS workflow_health_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component VARCHAR(100) NOT NULL, -- e.g. API, Database, Plugin, AI
    issue_type VARCHAR(100) NOT NULL,
    description TEXT,
    severity VARCHAR(20) DEFAULT 'High',
    resolved BOOLEAN DEFAULT false,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
