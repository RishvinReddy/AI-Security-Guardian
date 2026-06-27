import yaml

with open('generator/workflow-spec.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# Shift all sections by 2 to make room for Trigger Layer and Asset Inventory
for sec in spec['sections']:
    sec['id'] += 2
    parts = sec['name'].split(" ", 1)
    if len(parts) == 2 and parts[0].isdigit():
        sec['name'] = f"{sec['id']:02d} {parts[1]}"

# Create Section 01: Trigger Layer
section_1 = {
    "id": 1,
    "name": "01 Trigger Layer",
    "color": 7,
    "manual_wiring": True,
    "nodes": [
        {
            "name": "Trigger_Webhook",
            "type": "n8n-nodes-base.webhook",
            "entrypoint": True,
            "x": 0, "y": 0,
            "parameters": {"path": "scan-trigger", "options": {}},
            "connections": {"main": [[{"node": "CODE_TriggerRouter", "type": "main", "index": 0}]]}
        },
        {
            "name": "Trigger_GitHub",
            "type": "n8n-nodes-base.githubTrigger",
            "entrypoint": True,
            "x": 0, "y": 150,
            "parameters": {"events": ["push"]},
            "connections": {"main": [[{"node": "CODE_TriggerRouter", "type": "main", "index": 0}]]}
        },
        {
            "name": "Trigger_Schedule",
            "type": "n8n-nodes-base.cron",
            "entrypoint": True,
            "x": 0, "y": 300,
            "parameters": {"triggerTimes": {"item": [{"mode": "everyDay", "hour": 2}]}},
            "connections": {"main": [[{"node": "CODE_TriggerRouter", "type": "main", "index": 0}]]}
        },
        {
            "name": "Trigger_Manual",
            "type": "n8n-nodes-base.manualTrigger",
            "entrypoint": True,
            "x": 0, "y": 450,
            "parameters": {},
            "connections": {"main": [[{"node": "CODE_TriggerRouter", "type": "main", "index": 0}]]}
        },
        {
            "name": "CODE_TriggerRouter",
            "type": "n8n-nodes-base.code",
            "exitpoint": True,
            "x": 400, "y": 200,
            "parameters": {
                "jsCode": """
const source = $node.Trigger_Webhook ? 'Webhook' : 
               $node.Trigger_GitHub ? 'GitHub' : 
               $node.Trigger_Schedule ? 'Schedule' : 'Manual';
               
return {
    trigger: {
        source: source,
        timestamp: new Date().toISOString(),
        initiated_by: 'system'
    }
};
"""
            },
            "connections": {"main": [[{"node": "CFG_Configuration", "type": "main", "index": 0}]]}
        }
    ]
}

# The existing Configuration is now Section 3.
# I need to connect TriggerRouter to CFG_Configuration manually since I shifted it.
# Actually, if I just place them sequentially and use auto-wiring for Section 3, wait, Section 1 is manual, Section 3 is auto?
# In my modified build.py, if a section is manual and exits, it sets `current_section_outputs`. 
# The next section will automatically connect its first nodes to `current_section_outputs`.
# So I don't need to manually connect to `CFG_Configuration`!
# Let me remove the manual connection to CFG_Configuration to let build.py handle it.
section_1['nodes'][-1]['connections'] = {}

# We also need Section 02: Asset Inventory (CMDB)
section_2 = {
    "id": 2,
    "name": "02 Asset Inventory",
    "color": 2,
    "manual_wiring": True,
    "nodes": [
        {
            "name": "DB_LoadAssetCMDB",
            "type": "n8n-nodes-base.postgres",
            "entrypoint": True,
            "continueOnFail": True,
            "credentials": {"postgres": {"id": "", "name": "Postgres account"}},
            "x": 0, "y": 200,
            "parameters": {
                "operation": "executeQuery",
                "query": "SELECT * FROM assets WHERE domain = '{{ $('CFG_Configuration').item.json.TARGET_DOMAIN }}' LIMIT 1"
            },
            "connections": {"main": [[{"node": "CODE_AttachAssetContext", "type": "main", "index": 0}]]}
        },
        {
            "name": "CODE_AttachAssetContext",
            "type": "n8n-nodes-base.code",
            "exitpoint": True,
            "x": 400, "y": 200,
            "parameters": {
                "jsCode": """
// Merge the trigger data, config data, and CMDB data into the global payload
const config = $items("CFG_Configuration")[0].json;
const cmdb = $json || { domain: config.TARGET_DOMAIN, environment: 'Unknown', criticality: 'Medium' };

return {
    ...config,
    asset_context: cmdb
};
"""
            },
            "connections": {}
        }
    ]
}

# Insert Section 1 at the beginning
spec['sections'].insert(0, section_1)
# Configuration is currently at index 1 (which will be Section 03).
# Wait, I want the flow to be Trigger -> Configuration -> Asset Inventory -> Asset Discovery.
# So:
# Index 0: Trigger Layer (Section 01)
# Index 1: Configuration (Section 02)
# Index 2: Asset Inventory (Section 03)

spec['sections'][1]['id'] = 2
spec['sections'][1]['name'] = "02 Configuration"

section_2['id'] = 3
section_2['name'] = "03 Asset Inventory"

spec['sections'].insert(2, section_2)

# Fix IDs for the rest
for i, sec in enumerate(spec['sections']):
    if i > 2:
        sec['id'] = i + 1
        parts = sec['name'].split(" ", 1)
        if len(parts) == 2 and parts[0].isdigit():
            sec['name'] = f"{sec['id']:02d} {parts[1]}"

with open('generator/workflow-spec.yaml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False)

print("Milestone 1 & 2 YAML generated successfully.")
