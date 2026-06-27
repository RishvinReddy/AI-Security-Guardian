import yaml

with open('generator/workflow-spec.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# Find Vulnerability Scanning index
vuln_idx = -1
for i, sec in enumerate(spec['sections']):
    if "Vulnerability Scanning" in sec['name']:
        vuln_idx = i
        break

# Insert 07b Cloud Security
spec['sections'].insert(vuln_idx + 1, {
    "id": vuln_idx + 2,
    "name": "Cloud Security",
    "color": 3,
    "manual_wiring": True,
    "nodes": [
        {
            "name": "Cloud_AWS_Prowler",
            "type": "n8n-nodes-base.executeCommand",
            "entrypoint": True,
            "x": 0, "y": 0,
            "parameters": {"command": "echo 'Mock AWS Prowler scan' && cat examples/mock_prowler.json || echo '{}'"},
            "connections": {"main": [[{"node": "CODE_CloudNormalizer", "type": "main", "index": 0}]]}
        },
        {
            "name": "Cloud_Azure_API",
            "type": "n8n-nodes-base.httpRequest",
            "entrypoint": True,
            "x": 0, "y": 150,
            "parameters": {"url": "https://management.azure.com/mock", "method": "GET"},
            "connections": {"main": [[{"node": "CODE_CloudNormalizer", "type": "main", "index": 0}]]}
        },
        {
            "name": "Cloud_GCP_API",
            "type": "n8n-nodes-base.httpRequest",
            "entrypoint": True,
            "x": 0, "y": 300,
            "parameters": {"url": "https://mock.googleapis.com", "method": "GET"},
            "connections": {"main": [[{"node": "CODE_CloudNormalizer", "type": "main", "index": 0}]]}
        },
        {
            "name": "CODE_CloudNormalizer",
            "type": "n8n-nodes-base.code",
            "exitpoint": True,
            "x": 400, "y": 150,
            "parameters": {
                "jsCode": """
// Mock normalization
const globalJson = $items("CFG_Configuration")[0].json;
globalJson.cloud_findings = [
    { provider: 'aws', resource_type: 's3', resource_id: 'bucket-1', risk: 'high' }
];
return globalJson;
"""
            },
            "connections": {}
        }
    ]
})

# Insert 07c Container Security
spec['sections'].insert(vuln_idx + 2, {
    "id": vuln_idx + 3,
    "name": "Container Security",
    "color": 4,
    "manual_wiring": True,
    "nodes": [
        {
            "name": "Container_Trivy_FS",
            "type": "n8n-nodes-base.executeCommand",
            "entrypoint": True,
            "x": 0, "y": 0,
            "parameters": {"command": "echo 'Mock Trivy FS scan'"},
            "connections": {"main": [[{"node": "CODE_ContainerNormalizer", "type": "main", "index": 0}]]}
        },
        {
            "name": "Container_Trivy_Image",
            "type": "n8n-nodes-base.executeCommand",
            "entrypoint": True,
            "x": 0, "y": 150,
            "parameters": {"command": "echo 'Mock Trivy Image scan'"},
            "connections": {"main": [[{"node": "CODE_ContainerNormalizer", "type": "main", "index": 0}]]}
        },
        {
            "name": "Container_Trivy_SBOM",
            "type": "n8n-nodes-base.executeCommand",
            "entrypoint": True,
            "x": 0, "y": 300,
            "parameters": {"command": "echo 'Mock Trivy SBOM'"},
            "connections": {"main": [[{"node": "CODE_ContainerNormalizer", "type": "main", "index": 0}]]}
        },
        {
            "name": "CODE_ContainerNormalizer",
            "type": "n8n-nodes-base.code",
            "exitpoint": True,
            "x": 400, "y": 150,
            "parameters": {
                "jsCode": """
// Mock normalization
const globalJson = $items("CODE_CloudNormalizer")[0].json;
globalJson.container_findings = [
    { image_name: 'nginx:latest', vulnerabilities: 5, secrets: 1 }
];
return globalJson;
"""
            },
            "connections": {}
        }
    ]
})

# Update Risk Engine to include Cloud and Container exposure
for sec in spec['sections']:
    if "Risk Engine" in sec['name']:
        for node in sec['nodes']:
            if node['name'] == "CODE_RiskEngine":
                node['parameters']['jsCode'] = """
const globalJson = $json;
let score = 50;
let factors = [];

if (globalJson.vulnerabilities && globalJson.vulnerabilities.length > 0) {
    score += 20;
    factors.push("Vulnerabilities detected");
}

if (globalJson.cloud_findings && globalJson.cloud_findings.length > 0) {
    score += 15;
    factors.push("Cloud misconfigurations detected");
}

if (globalJson.container_findings && globalJson.container_findings.length > 0) {
    score += 10;
    factors.push("Container vulnerabilities detected");
}

if (globalJson.asset_context && globalJson.asset_context.criticality === 'Critical') {
    score += 10;
    factors.push("Critical business asset");
}

globalJson.risk_score = Math.min(score, 100);
globalJson.risk_factors = factors;

return globalJson;
"""

# Find Ticketing & Incident Management index
ticket_idx = -1
for i, sec in enumerate(spec['sections']):
    if "Ticketing & Incident Management" in sec['name']:
        ticket_idx = i
        break

# Insert Notification & Approval Engine
spec['sections'].insert(ticket_idx + 1, {
    "id": ticket_idx + 2,
    "name": "Notification & Approval Engine",
    "color": 8,
    "manual_wiring": True,
    "nodes": [
        {
            "name": "CODE_NotificationPolicyEngine",
            "type": "n8n-nodes-base.code",
            "entrypoint": True,
            "x": 0, "y": 200,
            "parameters": {
                "jsCode": """
const globalJson = $json;
const priority = (globalJson.incident || {}).priority || 'P4';
const policy = { require_approval: false, channels: [] };

if (priority === 'P1') {
    policy.require_approval = true;
    policy.channels = ['Slack', 'Email'];
} else if (priority === 'P2') {
    policy.channels = ['Slack', 'Email'];
} else if (priority === 'P3') {
    policy.channels = ['Slack'];
}

globalJson.notification_policy = policy;
return globalJson;
"""
            },
            "connections": {"main": [[{"node": "IF_RequiresApproval", "type": "main", "index": 0}]]}
        },
        {
            "name": "IF_RequiresApproval",
            "type": "n8n-nodes-base.if",
            "x": 300, "y": 200,
            "parameters": {
                "conditions": {
                    "boolean": [{"value1": "={{ $json.notification_policy.require_approval }}", "value2": True}]
                }
            },
            "connections": {
                "main": [
                    [{"node": "WAIT_ForApproval", "type": "main", "index": 0}], # TRUE
                    [{"node": "CODE_NotificationRouter", "type": "main", "index": 0}] # FALSE
                ]
            }
        },
        {
            "name": "WAIT_ForApproval",
            "type": "n8n-nodes-base.wait",
            "x": 600, "y": 100,
            "parameters": {
                "resume": "webhook",
                "webhookPath": "approve-incident"
            },
            "connections": {"main": [[{"node": "CODE_EscalationLogic", "type": "main", "index": 0}]]}
        },
        {
            "name": "CODE_EscalationLogic",
            "type": "n8n-nodes-base.code",
            "x": 900, "y": 100,
            "parameters": {
                "jsCode": """
// If wait timeout hit, escalate
$json.incident.escalated = true;
return $json;
"""
            },
            "connections": {"main": [[{"node": "CODE_NotificationRouter", "type": "main", "index": 0}]]}
        },
        {
            "name": "CODE_NotificationRouter",
            "type": "n8n-nodes-base.code",
            "x": 900, "y": 300,
            "parameters": {
                "jsCode": """
// Routes to different channels based on policy.channels
return $json;
"""
            },
            "connections": {"main": [[{"node": "HTTP_SlackWebhook", "type": "main", "index": 0}]]}
        },
        {
            "name": "HTTP_SlackWebhook",
            "type": "n8n-nodes-base.httpRequest",
            "exitpoint": True,
            "x": 1200, "y": 300,
            "parameters": {
                "url": "https://hooks.slack.com/services/mock",
                "method": "POST"
            },
            "connections": {}
        }
    ]
})

# Re-number all sections sequentially
for i, sec in enumerate(spec['sections']):
    sec['id'] = i + 1
    parts = sec['name'].split(" ", 1)
    if len(parts) == 2 and parts[0].isdigit():
        sec['name'] = f"{sec['id']:02d} {parts[1]}"
    elif not sec['name'][0].isdigit():
        sec['name'] = f"{sec['id']:02d} {sec['name']}"

# Prepend AI_IncidentCommander to Multi-Agent AI System
for sec in spec['sections']:
    if "Multi-Agent AI System" in sec['name']:
        commander_node = {
            "name": "AI_IncidentCommander",
            "type": "n8n-nodes-base.httpRequest",
            "entrypoint": True,
            "x": -300, "y": 200,
            "parameters": {
                "url": "https://api.openai.com/v1/chat/completions",
                "method": "POST",
                "sendBody": True,
                "bodyParameters": {
                    "parameters": [
                        {"name": "model", "value": "gpt-4-turbo"},
                        {"name": "messages", "value": '=[{"role": "system", "content": "Correlate multiple raw findings, cloud misconfigurations, and container vulnerabilities into a single incident."}, {"role": "user", "content": "{{ JSON.stringify($json) }}"}]'}
                    ]
                }
            },
            "connections": {"main": [[{"node": "AI_SecurityAnalyst", "type": "main", "index": 0}]]}
        }
        # Remove entrypoint from AI_SecurityAnalyst
        for node in sec['nodes']:
            if node['name'] == 'AI_SecurityAnalyst':
                if 'entrypoint' in node:
                    del node['entrypoint']
        # Add commander node
        sec['nodes'].insert(0, commander_node)
        break

with open('generator/workflow-spec.yaml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False)

print("Milestone 5 & 6 YAML generated successfully.")
