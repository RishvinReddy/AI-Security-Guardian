# AI Security Guardian Validation Suite

To ensure the platform operates reliably, follow these validation checks before pushing updates to production.

## 1. Component Tests

| Area | Test Procedure | Expected Result |
| :--- | :--- | :--- |
| **Workflow** | Import `AI_Security_Guardian_Mega.json` into a fresh n8n instance. | No import errors. All nodes connected. |
| **Database** | Run `init.sql` on a fresh PostgreSQL container. | 35 tables created successfully without conflicts. |
| **API Gateway** | Send `GET /api/v1/health` with a valid Auth token. | Returns 200 OK and valid JSON response. |
| **RBAC** | Send `POST /api/v1/scan` with an Invalid Token. | Returns 401 Unauthorized via the RBAC Validator. |
| **Plugin Manager** | Disable all plugins in DB, run a scan. | Normalizer catches 0 results, no scanner logic executed. |
| **Risk Engine** | Submit a mock payload with 1 Critical CVE and an IaC `public bucket` violation. | Output Risk Score is calculated deterministically (e.g., 55). |

## 2. Full End-to-End Test

1. Seed the PostgreSQL database with an authorized User and API Key.
2. Ensure the `CFG_Configuration` node is set to a safe, authorized test domain.
3. Trigger `POST /api/v1/scan`.
4. **Verification Checklist:**
    - [ ] `executions` table registers a new entry.
    - [ ] Plugin Manager triggers at least one scanner.
    - [ ] Normalizer yields a formatted finding.
    - [ ] Risk Engine applies a severity score.
    - [ ] `platform_events` registers the outbound event (with correlation IDs).
    - [ ] AI Metrics (cost, tokens) are logged to `ai_metrics` table.
