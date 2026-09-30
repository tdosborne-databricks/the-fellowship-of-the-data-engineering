# the-fellowship-of-the-data-engineering

Data engineering codebase for the `middle_earth` schema on Databricks. The
catalog name varies by workspace — see `AGENTS.md` for the dynamic discovery
pattern.

## Architecture

- **Production schema:** `<catalog>.middle_earth` — READ-ONLY for all users
- **Sandbox schema:** `<catalog>.middle_earth_sandbox` — writable for testing fixes
- **Governance:** Row-level security on `events`, column masking on `artifacts.secret_weakness`

## Repo Structure

```
pipelines/
  sync_event_outcomes.py   — Nightly ETL: syncs event outcomes to character status
  dedup_artifacts.py       — Weekly: detects duplicate artifact records
scripts/
  populate_sandbox.sql     — Copies production tables into sandbox (governance applies)
fixes/
  (agent-authored fix scripts land here via PR)
tests/
  (data quality checks land here via PR)
AGENTS.md                  — Good Hobbits investigation workflow for coding agents
```

## Setup

The bootstrap script that creates schemas, tables, governance, and grants is
maintained separately from this repo. Ask your workspace admin for access.

### Prerequisites

1. Databricks workspace with Unity Catalog enabled
2. A catalog containing the `middle_earth` and `middle_earth_sandbox` schemas
3. A `middle_earth_leadership` group configured for RLS and column masking
4. Git credential linked in User Settings → Linked Accounts

## How agents use this repo

1. Agent reads `AGENTS.md` for investigation workflow and hard constraints
2. Agent investigates data quality issues against production (read-only)
3. Agent queries UC data via the `system.ai.dbsql` MCP tool
4. Agent reads pipeline code to understand data flow and identify root causes
5. Agent writes a fix script and tests it against the sandbox schema
6. Agent pushes the fix to a branch and opens a PR
7. A human reviews and merges — agents never write to production
