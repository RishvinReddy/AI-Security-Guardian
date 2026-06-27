# Changelog

## [v3.0.0] - 2026-06-27

### Added
- **API Gateway & RBAC**: Exposed `/scan`, `/investigation`, `/dashboard` via Webhooks, secured via PostgreSQL Role-Based Access Control.
- **Plugin Manager**: Decoupled hardcoded scanners. Scanners are now dynamically orchestrated via the `plugins` database table.
- **Enterprise Security Support**: Inserted dedicated execution branches for Cloud (AWS Prowler, Azure, GCP) and Container (Trivy FS/Image/SBOM) security.
- **Infrastructure-as-Code (IaC)**: Integrated Terraform, Kubernetes, and Helm manifest scanning. IaC misconfigurations natively inflate the Risk Engine score.
- **Event Bus & SIEM Router**: Abstracted outbound communication. All incidents push to a central Event Bus, which routes to an Integration Hub (Slack, Jira) and SIEM Router (Splunk, Sentinel).
- **AI Investigation Gateway**: Evolved the multi-agent AI system into a dynamic query engine allowing users to ask natural language questions regarding incidents.
- **Observability Layer**: Workflow now actively monitors itself (tracking AI costs, token counts, execution latencies) and generates `workflow_health_incidents` upon degradation.
- **Executive Governance**: Added full compliance mapping (NIST, CIS, OWASP, SOC2) and an Executive Scorecard generator (calculating security, operational, and business KPIs).

### Changed
- Converted `AI_Security_Guardian.json` from a strict vulnerability scanning pipeline into a 700-node modular Platform Ecosystem.
- Database Schema expanded from 6 tables to 35 tables to support tracking changes, incidents, plugins, permissions, and metrics.
