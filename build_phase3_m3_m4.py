import yaml

with open('generator/workflow-spec.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# Shift sections for M3
# Everything from index 9 (currently Threat Intel Cache) and up gets shifted by 1
spec['sections'].insert(9, {
    "id": 10,
    "name": "10 Change Detection Engine",
    "color": 1,
    "manual_wiring": True,
    "nodes": [
        {
            "name": "CODE_ChangeClassifier",
            "type": "n8n-nodes-base.code",
            "entrypoint": True,
            "x": 0, "y": 200,
            "parameters": {
                "jsCode": """
const globalJson = $json;
const deltas = globalJson.historical;
const changes = [];

if (deltas && deltas.new_ports && deltas.new_ports.length > 0) {
    changes.push({ type: 'NEW_EXPOSURE', severity: 'HIGH', confidence: 0.98 });
}
if (deltas && deltas.new_cves && deltas.new_cves.length > 0) {
    changes.push({ type: 'SECURITY_REGRESSION', severity: 'CRITICAL', confidence: 0.95 });
}
if (deltas && deltas.resolved_cves && deltas.resolved_cves.length > 0) {
    changes.push({ type: 'REMEDIATION_CONFIRMED', severity: 'LOW', confidence: 0.99 });
}

globalJson.changes = changes;
return globalJson;
"""
            },
            "connections": {"main": [[{"node": "CODE_ChangePriority", "type": "main", "index": 0}]]}
        },
        {
            "name": "CODE_ChangePriority",
            "type": "n8n-nodes-base.code",
            "exitpoint": True,
            "x": 300, "y": 200,
            "parameters": {
                "jsCode": """
const globalJson = $json;
const assetContext = globalJson.asset_context || { criticality: 'Medium' };

globalJson.changes.forEach(change => {
    change.business_impact = assetContext.criticality;
});

return globalJson;
"""
            },
            "connections": {}
        }
    ]
})

# Shift sections for M4
# Find Risk Engine index
risk_idx = -1
for i, sec in enumerate(spec['sections']):
    if "Risk Engine" in sec['name']:
        risk_idx = i
        break

# Insert Ticketing & Incident Management right after Risk Engine
spec['sections'].insert(risk_idx + 1, {
    "id": risk_idx + 2,
    "name": f"{risk_idx + 2:02d} Ticketing & Incident Management",
    "color": 8,
    "manual_wiring": True,
    "nodes": [
        {
            "name": "CODE_IncidentCorrelator",
            "type": "n8n-nodes-base.code",
            "entrypoint": True,
            "x": 0, "y": 200,
            "parameters": {
                "jsCode": """
const globalJson = $json;
const findings = globalJson.vulnerabilities || [];
globalJson.incident = {
    title: `Incident: Multiple Findings on ${globalJson.TARGET_DOMAIN}`,
    finding_count: findings.length,
    related_findings: findings.map(f => f.hash || f.name)
};
return globalJson;
"""
            },
            "connections": {"main": [[{"node": "CODE_PriorityMatrix", "type": "main", "index": 0}]]}
        },
        {
            "name": "CODE_PriorityMatrix",
            "type": "n8n-nodes-base.code",
            "x": 300, "y": 200,
            "parameters": {
                "jsCode": """
const globalJson = $json;
const riskScore = globalJson.risk_score || 0;
const criticality = (globalJson.asset_context || {}).criticality || 'Medium';

let priority = 'P4';
if (riskScore > 90 && criticality === 'Critical') priority = 'P1';
else if (riskScore > 80) priority = 'P2';
else if (riskScore > 60) priority = 'P3';

globalJson.incident.priority = priority;
return globalJson;
"""
            },
            "connections": {"main": [[{"node": "CODE_TicketDeduplication", "type": "main", "index": 0}]]}
        },
        {
            "name": "CODE_TicketDeduplication",
            "type": "n8n-nodes-base.code",
            "x": 600, "y": 200,
            "parameters": {
                "jsCode": "// Mock deduplication logic\\n$json.incident.is_duplicate = false;\\nreturn $json;"
            },
            "connections": {"main": [[{"node": "IF_IsDuplicate", "type": "main", "index": 0}]]}
        },
        {
            "name": "IF_IsDuplicate",
            "type": "n8n-nodes-base.if",
            "x": 900, "y": 200,
            "parameters": {
                "conditions": {
                    "boolean": [{"value1": "={{ $json.incident.is_duplicate }}", "value2": True}]
                }
            },
            "connections": {
                "main": [
                    [{"node": "HTTP_GitHubUpdateIssue", "type": "main", "index": 0}], # TRUE
                    [{"node": "TicketRouter", "type": "main", "index": 0}] # FALSE
                ]
            }
        },
        {
            "name": "TicketRouter",
            "type": "n8n-nodes-base.code",
            "x": 1200, "y": 300,
            "parameters": {
                "jsCode": "return $json;"
            },
            "connections": {"main": [[{"node": "HTTP_GitHubCreateIssue", "type": "main", "index": 0}]]}
        },
        {
            "name": "HTTP_GitHubCreateIssue",
            "type": "n8n-nodes-base.httpRequest",
            "x": 1500, "y": 300,
            "parameters": {
                "url": "https://api.github.com/repos/mock/mock/issues",
                "method": "POST"
            },
            "connections": {"main": [[{"node": "DB_SaveIncidentState", "type": "main", "index": 0}]]}
        },
        {
            "name": "HTTP_GitHubUpdateIssue",
            "type": "n8n-nodes-base.httpRequest",
            "x": 1500, "y": 100,
            "parameters": {
                "url": "https://api.github.com/repos/mock/mock/issues/1",
                "method": "PATCH"
            },
            "connections": {"main": [[{"node": "DB_SaveIncidentState", "type": "main", "index": 0}]]}
        },
        {
            "name": "DB_SaveIncidentState",
            "type": "n8n-nodes-base.postgres",
            "exitpoint": True,
            "continueOnFail": True,
            "credentials": {"postgres": {"id": "", "name": "Postgres account"}},
            "x": 1800, "y": 200,
            "parameters": {
                "operation": "executeQuery",
                "query": "SELECT 1" # Mock
            },
            "connections": {}
        }
    ]
})

# Re-number all sections sequentially starting from 1
for i, sec in enumerate(spec['sections']):
    sec['id'] = i + 1
    parts = sec['name'].split(" ", 1)
    if len(parts) == 2 and parts[0].isdigit():
        sec['name'] = f"{sec['id']:02d} {parts[1]}"

with open('generator/workflow-spec.yaml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False)

print("Milestone 3 & 4 YAML generated successfully.")
