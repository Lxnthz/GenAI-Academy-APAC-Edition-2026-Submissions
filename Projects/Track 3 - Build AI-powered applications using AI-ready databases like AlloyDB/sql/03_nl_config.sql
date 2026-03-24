-- Track 3 default AlloyDB AI NL setup.
-- This script is intentionally defensive so setup can continue even when
-- AlloyDB AI NL functions differ across versions.

do $$
begin
	execute 'create extension if not exists alloydb_ai_nl cascade';
exception
	when others then
		raise notice 'alloydb_ai_nl extension setup skipped: %', sqlerrm;
end $$;

do $$
begin
	perform alloydb_ai_nl.g_create_configuration('track3_cfg');
exception
	when others then
		raise notice 'g_create_configuration skipped: %', sqlerrm;
end $$;

do $$
begin
	perform alloydb_ai_nl.generate_schema_context('track3_cfg');
exception
	when others then
		raise notice 'generate_schema_context skipped: %', sqlerrm;
end $$;

do $$
begin
	perform alloydb_ai_nl.apply_generated_schema_context('track3_cfg');
exception
	when others then
		raise notice 'apply_generated_schema_context skipped: %', sqlerrm;
end $$;

do $$
declare
	generated_sql text;
begin
	generated_sql := alloydb_ai_nl.get_sql('track3_cfg', 'show incident tickets') ->> 'sql';
	raise notice 'track3_cfg sample SQL: %', generated_sql;
exception
	when others then
		raise notice 'sample get_sql skipped: %', sqlerrm;
end $$;
