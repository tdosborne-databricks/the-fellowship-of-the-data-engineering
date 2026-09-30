# Good Hobbits — Middle-earth Data Engineering

This repo supports data quality investigation and remediation for the
Middle-earth data model on Databricks.

For the investigation workflow (discovery, investigation, fixes, git, hard
constraints), load the **Good Hobbits** skill from Unity Gateway. This file
provides only the project-specific context that the skill needs.

## Tooling

Use the `system.ai.dbsql` MCP tool to run SQL queries against Unity Catalog
tables. Do NOT use the Databricks CLI or shell commands for data access — they
will be blocked by network policies.

Do NOT inspect Git history, commit logs, diffs, deleted files, or prior commits
to infer data quality issues. Investigate using only current production data,
current pipeline code, and current repo contents.

## Data Context

### Discovering the catalog

The catalog name varies by workspace. At the start of every session, find it by
querying the information schema for the `middle_earth` schema:

```sql
SELECT catalog_name
FROM system.information_schema.schemata
WHERE schema_name = 'middle_earth';
```

Store the result and use it as `<catalog>` in all subsequent queries. If
multiple catalogs contain a `middle_earth` schema, ask the user which one to
use.

### Production schema: `<catalog>.middle_earth`

| Table | Description | Key columns |
| --- | --- | --- |
| characters | 15 characters of Middle-earth | name, race, allegiance, status (Alive/Deceased/Departed/Destroyed), email (PII), phone (PII) |
| events | 10 key events of the War of the Ring | event_name, participants (ARRAY\<STRING\>), outcome, classification (PUBLIC or CLASSIFIED) |
| artifacts | 6 artifacts and their bearers | name, bearer, status, secret_weakness (sensitive) |
| relationships | 14 character-to-character relationships | character_from, character_to, relationship_type, context |

These tables are interconnected. Characters appear in event participant lists,
bear artifacts, and have relationships to each other. If something looks wrong
in one table, cross-reference the others.

### Governance

* Row-level security on `events` — events with `classification = 'CLASSIFIED'`
  are only visible to members of the `palantir_bearers` group. If you see
  fewer events than expected, governance is filtering your view.
* Column masking on `artifacts.secret_weakness` — non-leadership users see
  masked values (`████ CLASSIFIED ████`) instead of the actual content.
* Production is read-only for all users. Nobody has MODIFY.

### Sandbox schema: `<catalog>.middle_earth_sandbox`

The sandbox schema starts **empty**. Populate it yourself before testing fixes
by using `CREATE TABLE AS SELECT` from production:

```sql
CREATE OR REPLACE TABLE <catalog>.middle_earth_sandbox.<table>
AS SELECT * FROM <catalog>.middle_earth.<table>;
```

**Important:** Your sandbox copy inherits your access level. If RLS hides rows
or column masking redacts values in production, those restrictions carry through
to the copy. If your sandbox appears to have fewer rows or masked values, that
is governance working as intended — document the gap and recommend someone with
broader access re-validate.

A helper script at `scripts/populate_sandbox.sql` automates this for all tables.

## Escalation

If access restrictions prevent you from fully diagnosing an issue, escalate
via Jira using the `fo_omnigent_demo_jira_mcp` MCP service:

1. Create a **Bug** ticket in the **FEINFRA** project
2. Include: summary of findings, what data was inaccessible and why it matters,
   and a link to this Omnigent session so a colleague can continue
3. Tag `jenni.wu@databricks.com` or `ash.kulkarni@databricks.com` as the
   assignee — both are `palantir_bearers` members and can see the full dataset

## Repo Layout

* `pipelines/` — ETL jobs that read and transform production data
* `fixes/` — Agent-authored fix scripts land here via PR
* `tests/` — Data quality checks that guard against recurrence
* `scripts/populate_sandbox.sql` — Copies production tables into sandbox
