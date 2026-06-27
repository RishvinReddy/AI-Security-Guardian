# Architecture

AI Security Guardian utilizes a distributed, asynchronous parallel pipeline built in n8n.

## Component Layering
1. **Trigger Layer**: CRON scheduling and manual invocation.
2. **Configuration Layer**: Injects environmental variables.
3. **Execution Layer**: Dispatches network requests (Nmap, Nuclei, Cloudflare DNS).
4. **Normalization Layer**: Code nodes parse tool-specific schemas into a global dictionary.
5. **Analysis Layer**: The Risk Engine uses math to clamp a score between 0-100.
6. **AI Layer**: OpenAI GPT-4o processes the JSON structure into human intelligence.
7. **Reporting Layer**: Data is sent to Postgres and Slack.
