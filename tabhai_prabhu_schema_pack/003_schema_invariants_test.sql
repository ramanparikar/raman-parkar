-- Read-only structural smoke test. Run after applying the draft to a LOCAL database.
-- This script does not insert, update, or delete any records.

do $$
declare
  actual_tables integer;
  expected_tables constant integer := 17;
  rls_disabled_tables text;
begin
  select count(*) into actual_tables
  from information_schema.tables
  where table_schema = 'scripture' and table_type = 'BASE TABLE';

  if actual_tables <> expected_tables then
    raise exception 'Expected % scripture tables, found %', expected_tables, actual_tables;
  end if;

  select string_agg(c.relname, ', ' order by c.relname)
    into rls_disabled_tables
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'scripture'
    and c.relkind = 'r'
    and not c.relrowsecurity;

  if rls_disabled_tables is not null then
    raise exception 'RLS is disabled on: %', rls_disabled_tables;
  end if;

  if not exists (
    select 1 from pg_constraint
    where connamespace = 'scripture'::regnamespace
      and conname = 'units_section_id_work_id_fkey'
  ) then
    raise exception 'Expected composite unit-to-section integrity constraint is missing';
  end if;

  if not exists (
    select 1 from pg_indexes
    where schemaname = 'scripture' and indexname = 'units_canonical_ref_key'
  ) then
    raise exception 'Canonical reference unique index is missing';
  end if;

  if not exists (
    select 1 from pg_constraint
    where connamespace = 'scripture'::regnamespace
      and conname = 'units_section_id_sequence_no_key'
  ) then
    raise exception 'Canonical unit sequence uniqueness constraint is missing';
  end if;

  if to_regprocedure('scripture.permission_grant_allows(uuid,uuid,text,text)') is null then
    raise exception 'Request-time permission grant helper is missing';
  end if;

  if to_regprocedure('scripture.search_published_content(text,text,integer)') is null then
    raise exception 'Rights-filtered scripture search function is missing';
  end if;

  raise notice 'Tabhai Prabhu schema smoke test passed: % tables, RLS enabled.', actual_tables;
end;
$$;
