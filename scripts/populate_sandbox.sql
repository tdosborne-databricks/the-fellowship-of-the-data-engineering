-- populate_sandbox.sql
-- Copies production tables into the sandbox schema for testing fixes.
--
-- Usage: Run this script before testing any DML fixes.
--
-- IMPORTANT: The copy runs as YOU, so Unity Catalog governance applies:
--   - Rows filtered by RLS will NOT appear in your sandbox copy
--   - Columns redacted by masking will contain masked values
--   - If your sandbox data seems incomplete, a user with broader access
--     should re-run this script to get a complete copy
--
-- The script discovers the catalog automatically by looking for the
-- middle_earth schema in the workspace's Unity Catalog.

-- Step 1: Identify the catalog (adjust if your workspace has multiple matches)
-- SELECT catalog_name FROM system.information_schema.schemata
-- WHERE schema_name = 'middle_earth';

-- Step 2: Populate sandbox tables (replace <catalog> with your catalog name)
CREATE OR REPLACE TABLE <catalog>.middle_earth_sandbox.characters
AS SELECT * FROM <catalog>.middle_earth.characters;

CREATE OR REPLACE TABLE <catalog>.middle_earth_sandbox.events
AS SELECT * FROM <catalog>.middle_earth.events;

CREATE OR REPLACE TABLE <catalog>.middle_earth_sandbox.artifacts
AS SELECT * FROM <catalog>.middle_earth.artifacts;

CREATE OR REPLACE TABLE <catalog>.middle_earth_sandbox.relationships
AS SELECT * FROM <catalog>.middle_earth.relationships;

-- Step 3: Verify row counts (compare with production to spot governance gaps)
SELECT 'characters' AS tbl, COUNT(*) AS sandbox_rows FROM <catalog>.middle_earth_sandbox.characters
UNION ALL
SELECT 'events', COUNT(*) FROM <catalog>.middle_earth_sandbox.events
UNION ALL
SELECT 'artifacts', COUNT(*) FROM <catalog>.middle_earth_sandbox.artifacts
UNION ALL
SELECT 'relationships', COUNT(*) FROM <catalog>.middle_earth_sandbox.relationships;
