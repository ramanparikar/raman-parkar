-- Tabhai Prabhu scripture knowledge base
-- DRAFT ONLY: NOT EXECUTED AGAINST ANY SUPABASE PROJECT.
-- Target: PostgreSQL 17 / Supabase. All objects live in a private schema.
-- Public access should be mediated by a reviewed Edge Function or security-invoker view.

begin;

create schema if not exists scripture;

create type scripture.section_kind as enum (
  'part', 'lila', 'canto', 'chapter', 'subchapter', 'other'
);
create type scripture.unit_kind as enum (
  'verse', 'sanskrit_verse', 'bengali_payar', 'prose', 'invocation',
  'song', 'prayer', 'caption', 'other'
);
create type scripture.content_kind as enum ('original', 'transliteration');
create type scripture.review_state as enum (
  'expected', 'imported', 'in_review', 'verified', 'rejected', 'incomplete'
);
create type scripture.rights_state as enum (
  'unknown', 'public_domain_confirmed', 'permission_pending',
  'licensed_for_use', 'restricted', 'not_cleared'
);
create type scripture.publication_state as enum (
  'private', 'eligible_for_publication', 'published', 'withdrawn'
);
create type scripture.commentary_kind as enum (
  'purport', 'commentary', 'lecture_excerpt', 'editorial_note', 'other'
);

create table scripture.works (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  canonical_title text not null,
  alternate_titles text[] not null default '{}',
  work_language text,
  description text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint works_code_format check (code ~ '^[A-Z][A-Z0-9_]*$')
);

create table scripture.editions (
  id uuid primary key default gen_random_uuid(),
  work_id uuid not null references scripture.works(id) on delete restrict,
  edition_code text not null,
  title text not null,
  editor_or_translator text,
  publisher text,
  publication_year integer,
  isbn text,
  edition_language text,
  source_description text,
  is_primary_reference boolean not null default false,
  created_at timestamptz not null default now(),
  unique (work_id, edition_code),
  unique (id, work_id),
  constraint edition_year_valid check (publication_year is null or publication_year between 1400 and 2200)
);

create table scripture.sections (
  id uuid primary key default gen_random_uuid(),
  work_id uuid not null references scripture.works(id) on delete restrict,
  edition_id uuid references scripture.editions(id) on delete restrict,
  parent_section_id uuid,
  section_kind scripture.section_kind not null,
  canonical_code text,
  canonical_title text not null,
  sequence_no integer not null,
  edition_label text,
  notes text,
  created_at timestamptz not null default now(),
  constraint section_sequence_nonnegative check (sequence_no >= 0),
  unique (id, work_id),
  unique nulls not distinct (work_id, edition_id, parent_section_id, sequence_no),
  foreign key (parent_section_id, work_id) references scripture.sections(id, work_id) on delete restrict,
  foreign key (edition_id, work_id) references scripture.editions(id, work_id) on delete restrict
);
create unique index sections_canonical_code_uq
  on scripture.sections(work_id, canonical_code) where canonical_code is not null;

create table scripture.units (
  id uuid primary key default gen_random_uuid(),
  work_id uuid not null references scripture.works(id) on delete restrict,
  section_id uuid not null references scripture.sections(id) on delete restrict,
  canonical_ref text not null unique,
  unit_kind scripture.unit_kind not null,
  sequence_no integer not null,
  canonical_label text,
  inventory_state scripture.review_state not null default 'expected',
  inventory_notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint unit_sequence_nonnegative check (sequence_no >= 0),
  unique (id, work_id),
  unique (section_id, sequence_no),
  foreign key (section_id, work_id) references scripture.sections(id, work_id) on delete restrict
);
create index units_work_section_sequence_idx on scripture.units(work_id, section_id, sequence_no);

create table scripture.unit_locators (
  id uuid primary key default gen_random_uuid(),
  work_id uuid not null,
  unit_id uuid not null,
  edition_id uuid not null,
  section_label text,
  chapter_label text,
  verse_label text,
  page_start text,
  page_end text,
  locator_note text,
  source_id uuid,
  created_at timestamptz not null default now(),
  unique (unit_id, edition_id),
  foreign key (unit_id, work_id) references scripture.units(id, work_id) on delete cascade,
  foreign key (edition_id, work_id) references scripture.editions(id, work_id) on delete restrict
);

create table scripture.sources (
  id uuid primary key default gen_random_uuid(),
  edition_id uuid references scripture.editions(id) on delete restrict,
  source_type text not null check (source_type in ('print_book','publisher_website','licensed_digital','public_domain_digital','manuscript','archive','other')),
  title text not null,
  publisher_or_host text,
  source_url text,
  isbn text,
  accessed_at timestamptz,
  source_locator text,
  file_sha256 text,
  source_notes text,
  created_at timestamptz not null default now(),
  constraint source_hash_format check (file_sha256 is null or file_sha256 ~ '^[0-9a-fA-F]{64}$')
);
alter table scripture.unit_locators
  add constraint unit_locators_source_fk foreign key (source_id) references scripture.sources(id) on delete set null;

create table scripture.rights_holders (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  website_url text,
  contact_reference text,
  notes text,
  created_at timestamptz not null default now(),
  unique (name)
);

create table scripture.permission_grants (
  id uuid primary key default gen_random_uuid(),
  rights_holder_id uuid references scripture.rights_holders(id) on delete restrict,
  edition_id uuid not null references scripture.editions(id) on delete restrict,
  permission_title text not null,
  permission_reference text,
  evidence_source_id uuid references scripture.sources(id) on delete set null,
  rights_state scripture.rights_state not null default 'permission_pending',
  permitted_actions text[] not null default '{}',
  permitted_languages text[] not null default '{}',
  territory text,
  starts_on date,
  expires_on date,
  public_display_allowed boolean not null default false,
  search_indexing_allowed boolean not null default false,
  embeddings_allowed boolean not null default false,
  ai_retrieval_allowed boolean not null default false,
  redistribution_allowed boolean not null default false,
  restrictions text,
  reviewed_by text,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  unique (id, edition_id),
  constraint permission_dates_valid check (expires_on is null or starts_on is null or expires_on >= starts_on),
  constraint permission_license_evidence check (rights_state <> 'licensed_for_use' or (rights_holder_id is not null and permission_reference is not null and evidence_source_id is not null and reviewed_by is not null and reviewed_at is not null))
);

create table scripture.import_batches (
  id uuid primary key default gen_random_uuid(),
  batch_name text not null,
  source_id uuid references scripture.sources(id) on delete restrict,
  edition_id uuid references scripture.editions(id) on delete restrict,
  imported_by text,
  import_method text,
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  batch_notes text,
  created_at timestamptz not null default now(),
  constraint import_batch_dates_valid check (completed_at is null or completed_at >= started_at)
);

create table scripture.unit_texts (
  id uuid primary key default gen_random_uuid(),
  work_id uuid not null,
  unit_id uuid not null,
  edition_id uuid not null,
  content_kind scripture.content_kind not null,
  language_code text not null,
  script_code text,
  variant_label text not null default 'default',
  text_content text not null,
  normalized_search_text text,
  source_id uuid references scripture.sources(id) on delete restrict,
  permission_grant_id uuid,
  import_batch_id uuid references scripture.import_batches(id) on delete set null,
  review_state scripture.review_state not null default 'imported',
  rights_state scripture.rights_state not null default 'unknown',
  publication_state scripture.publication_state not null default 'private',
  verified_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (unit_id, edition_id, content_kind, language_code, variant_label),
  constraint text_content_not_blank check (length(btrim(text_content)) > 0),
  foreign key (unit_id, work_id) references scripture.units(id, work_id) on delete cascade,
  foreign key (edition_id, work_id) references scripture.editions(id, work_id) on delete restrict,
  foreign key (permission_grant_id, edition_id) references scripture.permission_grants(id, edition_id) on delete restrict,
  constraint unit_text_publication_gate check (publication_state not in ('eligible_for_publication','published') or (review_state = 'verified' and rights_state in ('public_domain_confirmed','licensed_for_use'))),
  constraint unit_text_rights_evidence check ((rights_state <> 'public_domain_confirmed' or source_id is not null) and (rights_state <> 'licensed_for_use' or permission_grant_id is not null))
);
create index unit_texts_lookup_idx on scripture.unit_texts(unit_id, edition_id, content_kind, language_code);

create table scripture.translations (
  id uuid primary key default gen_random_uuid(),
  work_id uuid not null,
  unit_id uuid not null,
  edition_id uuid not null,
  language_code text not null,
  translation_text text not null,
  translator_or_editor text,
  source_id uuid references scripture.sources(id) on delete restrict,
  permission_grant_id uuid,
  import_batch_id uuid references scripture.import_batches(id) on delete set null,
  review_state scripture.review_state not null default 'imported',
  rights_state scripture.rights_state not null default 'unknown',
  publication_state scripture.publication_state not null default 'private',
  verified_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint translation_not_blank check (length(btrim(translation_text)) > 0),
  foreign key (unit_id, work_id) references scripture.units(id, work_id) on delete cascade,
  foreign key (edition_id, work_id) references scripture.editions(id, work_id) on delete restrict,
  foreign key (permission_grant_id, edition_id) references scripture.permission_grants(id, edition_id) on delete restrict,
  constraint translation_publication_gate check (publication_state not in ('eligible_for_publication','published') or (review_state = 'verified' and rights_state in ('public_domain_confirmed','licensed_for_use'))),
  constraint translation_rights_evidence check ((rights_state <> 'public_domain_confirmed' or source_id is not null) and (rights_state <> 'licensed_for_use' or permission_grant_id is not null))
);
create index translations_unit_language_idx on scripture.translations(unit_id, language_code, edition_id);

create table scripture.word_meanings (
  id uuid primary key default gen_random_uuid(),
  work_id uuid not null,
  unit_id uuid not null,
  edition_id uuid not null,
  language_code text not null,
  token_sequence integer not null,
  source_token text not null,
  token_transliteration text,
  meaning_text text not null,
  source_id uuid references scripture.sources(id) on delete restrict,
  permission_grant_id uuid,
  import_batch_id uuid references scripture.import_batches(id) on delete set null,
  review_state scripture.review_state not null default 'imported',
  rights_state scripture.rights_state not null default 'unknown',
  publication_state scripture.publication_state not null default 'private',
  created_at timestamptz not null default now(),
  constraint word_token_sequence_nonnegative check (token_sequence >= 0),
  constraint word_meaning_not_blank check (length(btrim(meaning_text)) > 0),
  unique (unit_id, edition_id, language_code, token_sequence),
  foreign key (unit_id, work_id) references scripture.units(id, work_id) on delete cascade,
  foreign key (edition_id, work_id) references scripture.editions(id, work_id) on delete restrict,
  foreign key (permission_grant_id, edition_id) references scripture.permission_grants(id, edition_id) on delete restrict,
  constraint word_meaning_publication_gate check (publication_state not in ('eligible_for_publication','published') or (review_state = 'verified' and rights_state in ('public_domain_confirmed','licensed_for_use'))),
  constraint word_meaning_rights_evidence check ((rights_state <> 'public_domain_confirmed' or source_id is not null) and (rights_state <> 'licensed_for_use' or permission_grant_id is not null))
);

create table scripture.commentaries (
  id uuid primary key default gen_random_uuid(),
  work_id uuid not null,
  unit_id uuid not null,
  edition_id uuid not null,
  commentary_kind scripture.commentary_kind not null,
  author text not null,
  language_code text not null,
  commentary_text text not null,
  source_id uuid references scripture.sources(id) on delete restrict,
  permission_grant_id uuid,
  import_batch_id uuid references scripture.import_batches(id) on delete set null,
  review_state scripture.review_state not null default 'imported',
  rights_state scripture.rights_state not null default 'unknown',
  publication_state scripture.publication_state not null default 'private',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint commentary_not_blank check (length(btrim(commentary_text)) > 0),
  foreign key (unit_id, work_id) references scripture.units(id, work_id) on delete cascade,
  foreign key (edition_id, work_id) references scripture.editions(id, work_id) on delete restrict,
  foreign key (permission_grant_id, edition_id) references scripture.permission_grants(id, edition_id) on delete restrict,
  constraint commentary_publication_gate check (publication_state not in ('eligible_for_publication','published') or (review_state = 'verified' and rights_state in ('public_domain_confirmed','licensed_for_use'))),
  constraint commentary_rights_evidence check ((rights_state <> 'public_domain_confirmed' or source_id is not null) and (rights_state <> 'licensed_for_use' or permission_grant_id is not null))
);

create table scripture.topics (
  id uuid primary key default gen_random_uuid(),
  parent_topic_id uuid references scripture.topics(id) on delete restrict,
  topic_slug text not null unique,
  topic_name text not null,
  description text,
  language_code text not null default 'en',
  created_at timestamptz not null default now()
);

create table scripture.unit_topics (
  unit_id uuid not null references scripture.units(id) on delete cascade,
  topic_id uuid not null references scripture.topics(id) on delete cascade,
  relevance_note text,
  assigned_by text,
  verified boolean not null default false,
  created_at timestamptz not null default now(),
  primary key (unit_id, topic_id)
);

create table scripture.verification_events (
  id uuid primary key default gen_random_uuid(),
  entity_type text not null check (entity_type in ('unit','unit_text','translation','word_meaning','commentary','locator')),
  entity_id uuid not null,
  previous_state text,
  new_state text not null,
  verification_method text,
  verifier text,
  evidence_source_id uuid references scripture.sources(id) on delete set null,
  notes text,
  created_at timestamptz not null default now()
);
create index verification_events_entity_idx on scripture.verification_events(entity_type, entity_id, created_at desc);

create table scripture.import_batch_items (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references scripture.import_batches(id) on delete cascade,
  entity_type text not null check (entity_type in ('unit','unit_text','translation','word_meaning','commentary','locator')),
  entity_id uuid not null,
  item_state text not null check (item_state in ('queued','imported','skipped','failed','verified')),
  message text,
  created_at timestamptz not null default now()
);
create index import_batch_items_batch_idx on scripture.import_batch_items(batch_id, item_state);

create or replace function scripture.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger works_set_updated_at before update on scripture.works
for each row execute function scripture.set_updated_at();
create trigger units_set_updated_at before update on scripture.units
for each row execute function scripture.set_updated_at();
create trigger unit_texts_set_updated_at before update on scripture.unit_texts
for each row execute function scripture.set_updated_at();
create trigger translations_set_updated_at before update on scripture.translations
for each row execute function scripture.set_updated_at();
create trigger commentaries_set_updated_at before update on scripture.commentaries
for each row execute function scripture.set_updated_at();

do $$
declare t record;
begin
  for t in
    select tablename
    from pg_tables
    where schemaname = 'scripture'
  loop
    execute format('alter table scripture.%I enable row level security', t.tablename);
  end loop;
end;
$$;

commit;

-- NOT INCLUDED ON PURPOSE:
-- No pgvector extension, public grants/policies, copyrighted imports, or production-table changes.
