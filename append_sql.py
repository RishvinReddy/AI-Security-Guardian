new_sql = """
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
"""
with open('database/init.sql', 'a') as f:
    f.write(new_sql)
print("SQL appended.")
