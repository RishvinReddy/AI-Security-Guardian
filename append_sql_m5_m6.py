new_sql = """
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
"""
with open('database/init.sql', 'a') as f:
    f.write(new_sql)
print("SQL M5/M6 appended.")
