import yaml
import json

with open('generator/workflow-spec.yaml', 'r') as f:
    spec = yaml.safe_load(f)

# Find and replace Section 12: Multi-Agent AI
section_idx = -1
for i, sec in enumerate(spec['sections']):
    if "Multi-Agent AI" in sec['name']:
        section_idx = i
        break

if section_idx == -1:
    print("Could not find Multi-Agent AI section.")
    exit(1)

section_12 = {
    "id": 12,
    "name": "12 Multi-Agent AI System",
    "color": 6,
    "manual_wiring": True,
    "nodes": []
}

agents = [
    ("SecurityAnalyst", "Analyze technical vulnerability data and classify technical risk."),
    ("ThreatAnalyst", "Analyze Threat Intelligence, EPSS, and KEV to determine exploitability."),
    ("ExecutiveAnalyst", "Translate technical risk into business impact based on Business Metrics."),
    ("RemediationPlanner", "Develop step-by-step remediation strategies and calculate estimated hours."),
    ("ComplianceAdvisor", "Map findings to CIS Controls, OWASP Top 10, NIST CSF, and SOC 2."),
    ("QualityValidator", "Review all previous AI outputs, ensure consistency, and generate final JSON report.")
]

x_offset = 0
for j, (name, prompt) in enumerate(agents):
    # Construct the JSON string carefully
    messages_payload = f'=[{{"role": "system", "content": "{prompt}"}}, {{"role": "user", "content": "{{{{ JSON.stringify($json) }}}}"}}]'
    
    node = {
        "name": f"AI_{name}",
        "type": "n8n-nodes-base.httpRequest",
        "x": x_offset, "y": 200,
        "parameters": {
            "url": "https://api.openai.com/v1/chat/completions",
            "method": "POST",
            "sendBody": True,
            "bodyParameters": {
                "parameters": [
                    {"name": "model", "value": "gpt-4-turbo"},
                    {"name": "messages", "value": messages_payload}
                ]
            }
        },
        "connections": {}
    }
    
    if j == 0:
        node['entrypoint'] = True
    
    if j < len(agents) - 1:
        node['connections']['main'] = [[{"node": f"AI_{agents[j+1][0]}", "type": "main", "index": 0}]]
    else:
        node['exitpoint'] = True
        
    section_12['nodes'].append(node)
    x_offset += 300

spec['sections'][section_idx] = section_12

with open('generator/workflow-spec.yaml', 'w') as f:
    yaml.dump(spec, f, sort_keys=False)

print("Milestone 6 YAML generated successfully.")
