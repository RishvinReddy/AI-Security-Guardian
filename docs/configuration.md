# Configuration

The `CFG_Configuration` node is the brain of the workflow.

## Variables
- `TARGET_DOMAIN`: The domain you wish to scan.
- `SCAN_PROFILE`: Options are `Standard` or `Deep`.
- `ENABLE_NMAP`: Boolean. Set to false to disable port scanning.
- `ENABLE_NUCLEI`: Boolean. Set to false to disable vulnerability scanning.
- `ENABLE_AI`: Boolean. Set to false to bypass OpenAI entirely and just log raw risk scores.
