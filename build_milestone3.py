import yaml

with open('generator/workflow-spec.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# 1. Update CFG_Configuration with TTLs
config_node = spec['sections'][0]['nodes'][1]
numbers = config_node['parameters']['values']['number']
ttls = [
    {"name": "TTL_NVD", "value": 604800},
    {"name": "TTL_EPSS", "value": 86400},
    {"name": "TTL_KEV", "value": 86400},
    {"name": "TTL_SHODAN", "value": 43200},
    {"name": "TTL_VIRUSTOTAL", "value": 43200},
    {"name": "TTL_GREYNOISE", "value": 21600},
    {"name": "TTL_ABUSEIPDB", "value": 86400}
]
# Only add if not exists
existing = {n['name'] for n in numbers}
for t in ttls:
    if t['name'] not in existing:
        numbers.append(t)

# 2. Re-write Section 08 Threat Intelligence with Caching
section_8 = {
    "id": 8,
    "name": "08 Threat Intelligence Cache",
    "color": 4,
    "manual_wiring": True,
    "nodes": []
}

# Entrypoint node
section_8['nodes'].append({
    "name": "CODE_ExtractFindings",
    "type": "n8n-nodes-base.code",
    "entrypoint": True,
    "x": 0, "y": 0,
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
y_offset = -600

for provider in providers:
    # 1. Feature Flag Check
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
                [{"node": f"DB_CacheLookup_{provider}", "type": "main", "index": 0}], # TRUE
                [{"node": f"SKIP_{provider}", "type": "main", "index": 0}]  # FALSE
            ]
        }
    })
    
    # 2. Cache Lookup
    section_8['nodes'].append({
        "name": f"DB_CacheLookup_{provider}",
        "type": "n8n-nodes-base.postgres",
        "continueOnFail": True,
        "credentials": {"postgres": {"id": "", "name": "Postgres account"}},
        "x": 600, "y": y_offset - 50,
        "parameters": {
            "operation": "executeQuery",
            "query": f"SELECT * FROM threat_intel_cache WHERE cache_key = $1 AND provider = '{provider}'"
        },
        "connections": {
            "main": [[{"node": f"IF_CacheValid_{provider}", "type": "main", "index": 0}]]
        }
    })

    # 3. Cache Validation (Valid vs Expired/Miss)
    section_8['nodes'].append({
        "name": f"IF_CacheValid_{provider}",
        "type": "n8n-nodes-base.if",
        "x": 900, "y": y_offset - 50,
        "parameters": {
            "conditions": {
                "boolean": [
                    {"value1": f"{{{{ $json.expires_at > new Date().toISOString() }}}}", "value2": True}
                ]
            }
        },
        "connections": {
            "main": [
                [{"node": f"RETURN_CACHE_{provider}", "type": "main", "index": 0}], # TRUE (Valid Cache)
                [{"node": f"HTTP_{provider}", "type": "main", "index": 0}]  # FALSE (Miss or Expired)
            ]
        }
    })

    # 4. HTTP API Call
    section_8['nodes'].append({
        "name": f"HTTP_{provider}",
        "type": "n8n-nodes-base.httpRequest",
        "continueOnFail": True,
        "x": 1200, "y": y_offset,
        "parameters": {
            "url": f"https://api.example.com/{provider.lower()}",
            "method": "GET"
        },
        "connections": {
            "main": [[{"node": f"IF_ApiSuccess_{provider}", "type": "main", "index": 0}]]
        }
    })
    
    # 5. API Success Check
    section_8['nodes'].append({
        "name": f"IF_ApiSuccess_{provider}",
        "type": "n8n-nodes-base.if",
        "x": 1500, "y": y_offset,
        "parameters": {
            "conditions": {
                "boolean": [
                    {"value1": f"{{{{ $json.status === 'success' }}}}", "value2": True}
                ]
            }
        },
        "connections": {
            "main": [
                [{"node": f"DB_SaveCache_{provider}", "type": "main", "index": 0}], # TRUE
                [{"node": f"IF_HasStaleCache_{provider}", "type": "main", "index": 0}] # FALSE
            ]
        }
    })
    
    # 6. Save Fresh Cache
    section_8['nodes'].append({
        "name": f"DB_SaveCache_{provider}",
        "type": "n8n-nodes-base.postgres",
        "continueOnFail": True,
        "credentials": {"postgres": {"id": "", "name": "Postgres account"}},
        "x": 1800, "y": y_offset - 50,
        "parameters": {
            "operation": "insert",
            "table": "threat_intel_cache",
            "columns": "cache_key, provider, entity_type, response, expires_at",
            "dataMode": "autoMapInputData"
        },
        "connections": {
            "main": [[{"node": "MERGE_ThreatIntel", "type": "main", "index": 0}]]
        }
    })
    
    # 7. Check if Stale Cache exists (Fallback)
    section_8['nodes'].append({
        "name": f"IF_HasStaleCache_{provider}",
        "type": "n8n-nodes-base.if",
        "x": 1800, "y": y_offset + 50,
        "parameters": {
            "conditions": {
                "boolean": [
                    {"value1": f"{{{{ $items('DB_CacheLookup_{provider}')[0].json.response ? true : false }}}}", "value2": True}
                ]
            }
        },
        "connections": {
            "main": [
                [{"node": f"RETURN_STALE_{provider}", "type": "main", "index": 0}], # TRUE
                [{"node": f"SKIP_{provider}", "type": "main", "index": 0}] # FALSE
            ]
        }
    })

    # 8. Return Valid Cache
    section_8['nodes'].append({
        "name": f"RETURN_CACHE_{provider}",
        "type": "n8n-nodes-base.code",
        "x": 1200, "y": y_offset - 150,
        "parameters": {
            "jsCode": f"return {{ provider: '{provider}', source: 'cache', data: $json }};"
        },
        "connections": {
            "main": [[{"node": "MERGE_ThreatIntel", "type": "main", "index": 0}]]
        }
    })
    
    # 9. Return Stale Cache
    section_8['nodes'].append({
        "name": f"RETURN_STALE_{provider}",
        "type": "n8n-nodes-base.code",
        "x": 2100, "y": y_offset,
        "parameters": {
            "jsCode": f"return {{ provider: '{provider}', source: 'stale_cache', data: $items('DB_CacheLookup_{provider}')[0].json }};"
        },
        "connections": {
            "main": [[{"node": "MERGE_ThreatIntel", "type": "main", "index": 0}]]
        }
    })

    # 10. SKIP / Failed
    section_8['nodes'].append({
        "name": f"SKIP_{provider}",
        "type": "n8n-nodes-base.code",
        "x": 2100, "y": y_offset + 100,
        "parameters": {
            "jsCode": f"return {{ provider: '{provider}', skipped: true }};"
        },
        "connections": {
            "main": [[{"node": "MERGE_ThreatIntel", "type": "main", "index": 0}]]
        }
    })
    
    y_offset += 350

# Merge Node
section_8['nodes'].append({
    "name": "MERGE_ThreatIntel",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 2.1,
    "x": 2500, "y": 450,
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
    "x": 2800, "y": 450,
    "parameters": {
        "jsCode": """
const globalJson = $items("CODE_CalculateDelta")[0].json;
globalJson.threat_intelligence = {
    sources: {}, summary: {}, confidence: 0,
    cache: { hits: 0, misses: 0, refreshes: 0, stale: 0 },
    metrics: { success_count: 0, skip_count: 0, fail_count: 0 }
};

let activeSources = 0;
for (const item of $input.all()) {
    const data = item.json;
    if (data.skipped) {
        globalJson.threat_intelligence.metrics.skip_count++;
    } else {
        globalJson.threat_intelligence.metrics.success_count++;
        activeSources++;
        
        // Track Cache Metrics
        if (data.source === 'cache') {
            globalJson.threat_intelligence.cache.hits++;
        } else if (data.source === 'stale_cache') {
            globalJson.threat_intelligence.cache.stale++;
        } else {
            globalJson.threat_intelligence.cache.refreshes++;
        }

        globalJson.threat_intelligence.sources[data.provider || 'unknown'] = {
            source_type: data.source || 'live_api',
            retrieved_at: new Date().toISOString(),
            confidence: 0.95
        };
    }
}

globalJson.threat_intelligence.confidence = activeSources > 0 ? (activeSources / 7) : 0;
return globalJson;
"""
    }
})

spec['sections'][7] = section_8

with open('generator/workflow-spec.yaml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False)

print("YAML updated for Milestone 3 successfully.")
