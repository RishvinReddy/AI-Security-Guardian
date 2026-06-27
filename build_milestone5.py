import yaml

with open('generator/workflow-spec.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# Shift sections 10, 11, 12 to 11, 12, 13
for sec in spec['sections']:
    if sec['id'] >= 10:
        sec['id'] += 1
        parts = sec['name'].split(" ", 1)
        if len(parts) == 2 and parts[0].isdigit():
            sec['name'] = f"{sec['id']:02d} {parts[1]}"

# Create Section 10: Security Intelligence Layer
section_10 = {
    "id": 10,
    "name": "10 Security Intelligence Layer",
    "color": 5,
    "manual_wiring": True,
    "nodes": []
}

# Entrypoint node
section_10['nodes'].append({
    "name": "CODE_ExtractRawMetrics",
    "type": "n8n-nodes-base.code",
    "entrypoint": True,
    "x": 0, "y": 200,
    "parameters": {
        "jsCode": "return $json;"
    },
    "connections": {
        "main": [
            [{"node": "CODE_OperationalMetrics", "type": "main", "index": 0}],
            [{"node": "CODE_SecurityMetrics", "type": "main", "index": 0}],
            [{"node": "CODE_ExecutiveMetrics", "type": "main", "index": 0}],
            [{"node": "CODE_BusinessMetrics", "type": "main", "index": 0}]
        ]
    }
})

engines = ["Operational", "Security", "Executive", "Business"]
y_offsets = [0, 150, 300, 450]

for i, eng in enumerate(engines):
    section_10['nodes'].append({
        "name": f"CODE_{eng}Metrics",
        "type": "n8n-nodes-base.code",
        "x": 400, "y": y_offsets[i],
        "parameters": {
            "jsCode": f"// Mock logic for {eng} Metrics\\nreturn {{ category: '{eng.lower()}', metrics: {{ score: Math.random() }} }};"
        },
        "connections": {
            "main": [[{"node": "MERGE_SecurityIntel", "type": "main", "index": 0}]]
        }
    })

section_10['nodes'].append({
    "name": "MERGE_SecurityIntel",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 2.1,
    "x": 700, "y": 200,
    "parameters": {
        "mode": "wait"
    },
    "connections": {
        "main": [[{"node": "CODE_SecurityIntelligenceAggregator", "type": "main", "index": 0}]]
    }
})

section_10['nodes'].append({
    "name": "CODE_SecurityIntelligenceAggregator",
    "type": "n8n-nodes-base.code",
    "x": 1000, "y": 200,
    "parameters": {
        "jsCode": """
const globalJson = $items("CODE_TrendConfidence")[0].json;

globalJson.security_intelligence = {
    operational: {},
    security: {},
    executive: {},
    business: {},
    generated_at: new Date().toISOString()
};

for (const item of $input.all()) {
    if (item.json.category === 'operational') globalJson.security_intelligence.operational = item.json.metrics;
    if (item.json.category === 'security') globalJson.security_intelligence.security = item.json.metrics;
    if (item.json.category === 'executive') globalJson.security_intelligence.executive = item.json.metrics;
    if (item.json.category === 'business') globalJson.security_intelligence.business = item.json.metrics;
}

return globalJson;
"""
    },
    "connections": {
        "main": [[{"node": "DB_SaveSecurityIntelligence", "type": "main", "index": 0}]]
    }
})

section_10['nodes'].append({
    "name": "DB_SaveSecurityIntelligence",
    "type": "n8n-nodes-base.postgres",
    "exitpoint": True,
    "continueOnFail": True,
    "credentials": {"postgres": {"id": "", "name": "Postgres account"}},
    "x": 1300, "y": 200,
    "parameters": {
        "operation": "insert",
        "table": "dashboard_metrics",
        "columns": "asset_id, operational_metrics, security_metrics, executive_metrics, business_metrics",
        "dataMode": "defineBelow",
        "values": {
            "value": [
                {"column": "asset_id", "value": "={{ $('CFG_Configuration').item.json.TARGET_DOMAIN }}"},
                {"column": "operational_metrics", "value": "={{ JSON.stringify($json.security_intelligence.operational) }}"},
                {"column": "security_metrics", "value": "={{ JSON.stringify($json.security_intelligence.security) }}"},
                {"column": "executive_metrics", "value": "={{ JSON.stringify($json.security_intelligence.executive) }}"},
                {"column": "business_metrics", "value": "={{ JSON.stringify($json.security_intelligence.business) }}"}
            ]
        }
    }
})

# Insert Section 10
spec['sections'].insert(9, section_10)

with open('generator/workflow-spec.yaml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False)

print("Milestone 5 YAML generated successfully.")
