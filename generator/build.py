import yaml
import json
import uuid

def generate_uuid():
    return str(uuid.uuid4())

def main():
    with open('generator/workflow-spec.yaml', 'r') as f:
        spec = yaml.safe_load(f)

    nodes = []
    connections = {}
    
    start_x = 0
    start_y = 0
    
    previous_section_outputs = []

    for section in spec['sections']:
        section_id = section['id']
        section_name = section['name']
        section_color = section['color']
        section_nodes = section.get('nodes', [])
        manual_wiring = section.get('manual_wiring', False)
        
        sticky_width = max(1000, len(section_nodes) * 200)
        sticky_height = 800 if manual_wiring else 400
        
        nodes.append({
            "id": generate_uuid(),
            "name": f"Sticky Note: {section_name}",
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": [start_x, start_y],
            "parameters": {
                "content": f"## {section_name}",
                "height": sticky_height,
                "width": sticky_width,
                "color": section_color
            }
        })
        
        current_section_outputs = []
        
        if manual_wiring:
            # MANUAL WIRING MODE
            for n_def in section_nodes:
                node_name = f"{n_def['name']}"
                node = {
                    "id": generate_uuid(),
                    "name": node_name,
                    "type": n_def['type'],
                    "typeVersion": n_def.get('typeVersion', 1),
                    "position": [start_x + n_def.get('x', 50), start_y + n_def.get('y', 100)],
                    "parameters": n_def.get('parameters', {})
                }
                if n_def.get('continueOnFail'):
                    node['continueOnFail'] = True
                if n_def.get('credentials'):
                    node['credentials'] = n_def['credentials']
                nodes.append(node)
                
                # Connect previous section to entrypoints
                if n_def.get('entrypoint'):
                    for prev_out in previous_section_outputs:
                        if prev_out not in connections:
                            connections[prev_out] = {"main": [[]]}
                        connections[prev_out]["main"][0].append({
                            "node": node_name,
                            "type": "main",
                            "index": 0
                        })
                
                # Collect exitpoints for the next section
                if n_def.get('exitpoint'):
                    current_section_outputs.append(node_name)
                    
                # Add custom connections defined in the YAML
                if n_def.get('connections'):
                    connections[node_name] = n_def['connections']
                    
            previous_section_outputs = current_section_outputs
        
        else:
            # AUTO WIRING MODE
            node_x = start_x + 50
            node_y = start_y + 100
            
            for idx, n_def in enumerate(section_nodes):
                node_name = f"{n_def['name']}"
                node = {
                    "id": generate_uuid(),
                    "name": node_name,
                    "type": n_def['type'],
                    "typeVersion": n_def.get('typeVersion', 1),
                    "position": [node_x, node_y],
                    "parameters": n_def.get('parameters', {})
                }
                if n_def.get('continueOnFail'):
                    node['continueOnFail'] = True
                if n_def.get('credentials'):
                    node['credentials'] = n_def['credentials']
                    
                nodes.append(node)
                current_section_outputs.append(node_name)
                
                for prev_out in previous_section_outputs:
                    if prev_out not in connections:
                        connections[prev_out] = {"main": [[]]}
                    connections[prev_out]["main"][0].append({
                        "node": node_name,
                        "type": "main",
                        "index": 0
                    })
                
                node_x += 200
                
            if len(current_section_outputs) > 1:
                merge_node_name = f"MERGE_{section_id}"
                nodes.append({
                    "id": generate_uuid(),
                    "name": merge_node_name,
                    "type": "n8n-nodes-base.merge",
                    "typeVersion": 2.1,
                    "position": [start_x + sticky_width - 150, start_y + 150],
                    "parameters": {
                        "mode": "wait"
                    }
                })
                
                for i, out_node in enumerate(current_section_outputs):
                    if out_node not in connections:
                        connections[out_node] = {"main": [[]]}
                    connections[out_node]["main"][0].append({
                        "node": merge_node_name,
                        "type": "main",
                        "index": i % 2 # Simplified routing
                    })
                previous_section_outputs = [merge_node_name]
            elif len(current_section_outputs) == 1:
                previous_section_outputs = current_section_outputs
            else:
                pass
                
        start_y += sticky_height + 100

    workflow = {
        "name": spec.get("name", "AI Security Guardian Mega Workflow"),
        "nodes": nodes,
        "connections": connections,
        "settings": {"executionOrder": "v1"}
    }
    
    with open('AI_Security_Guardian_Mega.json', 'w') as f:
        json.dump(workflow, f, indent=2)
        
    print("Mega Workflow compiled successfully to AI_Security_Guardian_Mega.json")

if __name__ == '__main__':
    main()
