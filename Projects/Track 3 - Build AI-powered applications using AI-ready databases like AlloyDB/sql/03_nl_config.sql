-- AlloyDB AI Natural Language setup placeholders.
-- Update these statements to match the exact syntax for your AlloyDB version.

-- Example extension enablement pattern (adjust if required):
-- create extension if not exists google_ml_integration cascade;

-- Example conceptual mappings for this dataset:
-- "urgent" -> urgency_score >= 70
-- "unresolved" -> status <> 'closed'
-- "payment issue" -> category = 'billing'

-- The application reads APP_NL_TO_SQL_TEMPLATE from env.
-- Set it to the SQL statement that returns a generated SQL text as first column.
-- Example template:
-- select generated_sql from alloydb_ai_nl('{question}')

select 'Update this file with AlloyDB AI NL setup for your project version.' as note;
