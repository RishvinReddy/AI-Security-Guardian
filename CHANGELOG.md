# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-06-27

### Added
- Mega Workflow (`AI_Security_Guardian_Mega.json`) compiling 15 logical sections.
- YAML Generator (`workflow-spec.yaml` + `build.py`) for automated compilation.
- Centralized Data Normalization with Asset Fingerprints.
- Deterministic Risk Engine combining CVSS, KEV, and Asset Exposure.
- OpenAI Integration for executive and technical summaries.
- PostgreSQL Schema (6 tables) for structured execution and findings logs.
- Docker Compose stack with n8n, Redis, and Postgres.

### Security
- Added `continueOnFail` error handling to prevent API timeouts from halting workflows.
- Implemented severity-based alert routing.
