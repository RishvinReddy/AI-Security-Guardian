import yaml

with open('generator/workflow-spec.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# 1. Update CFG_Configuration with new Feature Flags
config_node = spec['sections'][0]['nodes'][1]
booleans = config_node['parameters']['values']['boolean']
new_flags = [
    {"name": "ENABLE_NVD", "value": True},
    {"name": "ENABLE_EPSS", "value": True},
    {"name": "ENABLE_KEV", "value": True},
    {"name": "ENABLE_SHODAN", "value": False},
    {"name": "ENABLE_VIRUSTOTAL", "value": True},
    {"name": "ENABLE_GREYNOISE", "value": False},
    {"name": "ENABLE_ABUSEIPDB", "value": False}
]
booleans.extend(new_flags)

# 2. Re-write Section 08 Threat Intelligence with manual wiring
section_8 = {
    "id": 8,
    "name": "08 Threat Intelligence",
    "color": 4,
    "manual_wiring": True,
    "nodes": []
}

# Entrypoint node
section_8['nodes'].append({
    "name": "CODE_ExtractFindings",
    "type": "n8n-nodes-base.code",
    "entrypoint": True,
    "x": 0, "y": 200,
    "parameters": {
        "jsCode": "return $json.vulnerabilities || [];"
    },
    "connections": {
        "main": [[
            {"node": "IF_NVD", "type": "main", "index": 0},
            {"node": "IF_EPSS", "type": "main", "index": 0},
            {"node": "IF_KEV", "type": "main", "index": 0},
            {"node": "IF_Shodan", "type": "main", "index": 0},
            {"node": "IF_VirusTotal", "type": "main", "index": 0},
            {"node": "IF_GreyNoise", "type": "main", "index": 0},
            {"node": "IF_AbuseIPDB", "type": "main", "index": 0}
        ]]
    }
})

providers = ["NVD", "EPSS", "KEV", "Shodan", "VirusTotal", "GreyNoise", "AbuseIPDB"]
y_offset = 0

for provider in providers:
    # IF node
    section_8['nodes'].append({
        "name": f"IF_{provider}",
        "type": "n8n-nodes-base.if",
        "x": 300, "y": y_offset,
        "parameters": {
            "conditions": {
                "boolean": [
                    {"value1": f"{{{{ $('CFG_Configuration').item.json.ENABLE_{provider.upper()} }}}}", "value2": True}
                ]
            }
        },
        "connections": {
            "main": [
                [{"node": f"HTTP_{provider}", "type": "main", "index": 0}], # TRUE
                [{"node": f"SKIP_{provider}", "type": "main", "index": 0}]  # FALSE
            ]
        }
    })
    
    # HTTP Node (Mocked as success with metadata)
    section_8['nodes'].append({
        "name": f"HTTP_{provider}",
        "type": "n8n-nodes-base.httpRequest",
        "continueOnFail": True,
        "x": 600, "y": y_offset - 50,
        "parameters": {
            "url": f"https://api.example.com/{provider.lower()}",
            "method": "GET"
        },
        "connections": {
            "main": [[{"node": "MERGE_ThreatIntel", "type": "main", "index": 0}]]
        }
    })
    
    # SKIP Node
    section_8['nodes'].append({
        "name": f"SKIP_{provider}",
        "type": "n8n-nodes-base.code",
        "x": 600, "y": y_offset + 50,
        "parameters": {
            "jsCode": f"return {{ provider: '{provider}', skipped: true }};"
        },
        "connections": {
            "main": [[{"node": "MERGE_ThreatIntel", "type": "main", "index": 0}]]
        }
    })
    
    y_offset += 150

# Merge Node
section_8['nodes'].append({
    "name": "MERGE_ThreatIntel",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 2.1,
    "x": 900, "y": 450,
    "parameters": {
        "mode": "wait"
    },
    "connections": {
        "main": [[{"node": "CODE_ThreatIntelAggregator", "type": "main", "index": 0}]]
    }
})

# Aggregator Node
section_8['nodes'].append({
    "name": "CODE_ThreatIntelAggregator",
    "type": "n8n-nodes-base.code",
    "exitpoint": True,
    "x": 1200, "y": 450,
    "parameters": {
        "jsCode": """
// Reconstruct the global object and embed the aggregated threat intel
const globalJson = $items("CODE_CalculateDelta")[0].json;

globalJson.threat_intelligence = {
    sources: {},
    summary: {},
    confidence: 0,
    cache: {},
    metrics: {
        latency_ms: 420,
        success_count: 0,
        skip_count: 0
    }
};

let activeSources = 0;
// Example aggregation logic over merged items
for (const item of $input.all()) {
    const data = item.json;
    if (data.skipped) {
        globalJson.threat_intelligence.metrics.skip_count++;
    } else {
        globalJson.threat_intelligence.metrics.success_count++;
        activeSources++;
        // Attach metadata
        globalJson.threat_intelligence.sources[data.provider || 'unknown'] = {
            status: "success",
            retrieved_at: new Date().toISOString(),
            ttl: 86400,
            confidence: 0.95
        };
    }
}

// Confidence Calculation (mocked logic)
globalJson.threat_intelligence.confidence = activeSources > 0 ? (activeSources / 7) : 0;

return globalJson;
"""
    }
})

spec['sections'][7] = section_8

with open('generator/workflow-spec.yaml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False)

print("YAML updated successfully.")
