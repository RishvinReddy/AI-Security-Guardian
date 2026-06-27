import yaml

with open('generator/workflow-spec.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# Shift sections 9, 10, 11 to 10, 11, 12
for sec in spec['sections']:
    if sec['id'] >= 9:
        sec['id'] += 1
        # Update name prefix if it matches
        parts = sec['name'].split(" ", 1)
        if len(parts) == 2 and parts[0].isdigit():
            sec['name'] = f"{sec['id']:02d} {parts[1]}"

# Create Section 09: Trend Intelligence Engine
section_9 = {
    "id": 9,
    "name": "09 Trend Intelligence Engine",
    "color": 3,
    "manual_wiring": True,
    "nodes": []
}

# 1. DB Loaders (Serial for simplicity in n8n, but let's do one node that loads all context)
# For n8n, a single Postgres query can fetch 90 days of data and we process it in code.
section_9['nodes'].append({
    "name": "DB_LoadHistoricalTrends",
    "type": "n8n-nodes-base.postgres",
    "continueOnFail": True,
    "credentials": {"postgres": {"id": "", "name": "Postgres account"}},
    "entrypoint": True,
    "x": 0, "y": 300,
    "parameters": {
        "operation": "executeQuery",
        "query": "SELECT * FROM trend_analysis WHERE asset_id = '{{ $('CFG_Configuration').item.json.TARGET_DOMAIN }}' AND date >= CURRENT_DATE - 90 ORDER BY date ASC"
    },
    "connections": {
        "main": [
            [{"node": "CODE_EngineRiskTrend", "type": "main", "index": 0}],
            [{"node": "CODE_EngineFindingVelocity", "type": "main", "index": 0}],
            [{"node": "CODE_EngineAssetGrowth", "type": "main", "index": 0}],
            [{"node": "CODE_EngineScannerHealth", "type": "main", "index": 0}],
            [{"node": "CODE_EngineThreatEvolution", "type": "main", "index": 0}]
        ]
    }
})

engines = ["RiskTrend", "FindingVelocity", "AssetGrowth", "ScannerHealth", "ThreatEvolution"]
y_offsets = [0, 150, 300, 450, 600]

for i, eng in enumerate(engines):
    section_9['nodes'].append({
        "name": f"CODE_Engine{eng}",
        "type": "n8n-nodes-base.code",
        "x": 400, "y": y_offsets[i],
        "parameters": {
            "jsCode": f"// Mock logic for {eng}\\nreturn {{ engine: '{eng}', data: {{ trend: 'stable', value: Math.random() }} }};"
        },
        "connections": {
            "main": [[{"node": "MERGE_TrendEngines", "type": "main", "index": 0}]]
        }
    })

section_9['nodes'].append({
    "name": "MERGE_TrendEngines",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 2.1,
    "x": 700, "y": 300,
    "parameters": {
        "mode": "wait"
    },
    "connections": {
        "main": [[{"node": "CODE_TrendConfidence", "type": "main", "index": 0}]]
    }
})

section_9['nodes'].append({
    "name": "CODE_TrendConfidence",
    "type": "n8n-nodes-base.code",
    "exitpoint": True,
    "x": 1000, "y": 300,
    "parameters": {
        "jsCode": """
const globalJson = $items("CODE_ThreatIntelAggregator")[0].json;

globalJson.trend = {
    risk: {},
    findings: {},
    assets: {},
    scanner_health: {},
    threat_evolution: {},
    confidence: 0.95
};

for (const item of $input.all()) {
    if (item.json.engine === 'RiskTrend') globalJson.trend.risk = item.json.data;
    if (item.json.engine === 'FindingVelocity') globalJson.trend.findings = item.json.data;
    if (item.json.engine === 'AssetGrowth') globalJson.trend.assets = item.json.data;
    if (item.json.engine === 'ScannerHealth') globalJson.trend.scanner_health = item.json.data;
    if (item.json.engine === 'ThreatEvolution') globalJson.trend.threat_evolution = item.json.data;
}

return globalJson;
"""
    }
})

# Insert Section 9
spec['sections'].insert(8, section_9)

with open('generator/workflow-spec.yaml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False)

print("Milestone 4 YAML generated successfully.")
