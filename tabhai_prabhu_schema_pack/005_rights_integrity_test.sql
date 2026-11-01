-- Transactional integrity tests: all synthetic rows are rolled back.
begin;

do $$
declare
  v_work uuid;
  v_ed1 uuid;
  v_ed2 uuid;
  v_source uuid;
  v_holder uuid;
  v_grant uuid;
  v_expired_grant uuid;
  v_section uuid;
  v_unit uuid;
begin
  select id into v_work from scripture.works where code = 'BG';

  insert into scripture.editions (work_id, edition_code, title, edition_language)
  values (v_work, 'RIGHTS_TEST_EDITION_A', 'Synthetic rights test edition A', 'en')
  returning id into v_ed1;

  insert into scripture.editions (work_id, edition_code, title, edition_language)
  values (v_work, 'RIGHTS_TEST_EDITION_B', 'Synthetic rights test edition B', 'en')
  returning id into v_ed2;

  insert into scripture.sources (edition_id, source_type, title)
  values (v_ed1, 'other', 'Synthetic rights test source')
  returning id into v_source;

  insert into scripture.rights_holders (name, notes)
  values ('Synthetic Rights Holder - Test Only', 'Synthetic CI fixture; not a real rights holder')
  returning id into v_holder;

  insert into scripture.permission_grants (
    rights_holder_id, edition_id, permission_title, permission_reference,
    evidence_source_id, rights_state, permitted_actions, permitted_languages,
    public_display_allowed, search_indexing_allowed, embeddings_allowed,
    ai_retrieval_allowed, redistribution_allowed, reviewed_by, reviewed_at
  ) values (
    v_holder, v_ed1, 'Synthetic CI test grant', 'SYNTHETIC-TEST-GRANT',
    v_source, 'licensed_for_use', array['public_display','search_indexing'], array['sa'],
    true, true, false, false, false, 'CI fixture', now()
  ) returning id into v_grant;

  insert into scripture.permission_grants (
    rights_holder_id, edition_id, permission_title, permission_reference,
    evidence_source_id, rights_state, permitted_actions, permitted_languages,
    public_display_allowed, reviewed_by, reviewed_at, expires_on
  ) values (
    v_holder, v_ed1, 'Synthetic expired grant', 'SYNTHETIC-EXPIRED-GRANT',
    v_source, 'licensed_for_use', array['public_display'], array['sa'],
    true, 'CI fixture', now(), current_date - 1
  ) returning id into v_expired_grant;

  insert into scripture.sections (
    work_id, edition_id, section_kind, canonical_code, canonical_title, sequence_no
  ) values (v_work, null, 'chapter', 'BG.RIGHTS_TEST', 'Synthetic rights test section', 999)
  returning id into v_section;

  insert into scripture.units (
    work_id, section_id, canonical_ref, unit_kind, sequence_no, canonical_label
  ) values (v_work, v_section, 'BG.18.997', 'verse', 997, 'Synthetic test reference')
  returning id into v_unit;

  -- Matching edition grant is structurally valid (content remains private).
  insert into scripture.unit_texts (
    work_id, unit_id, edition_id, content_kind, language_code, text_content,
    permission_grant_id, rights_state, publication_state
  ) values (
    v_work, v_unit, v_ed1, 'original', 'sa', 'Synthetic test fixture only',
    v_grant, 'licensed_for_use', 'private'
  );

  update scripture.unit_texts
  set review_state = 'verified', publication_state = 'published'
  where unit_id = v_unit and edition_id = v_ed1 and content_kind = 'original';

  if not exists (
    select 1
    from scripture.search_published_content('Synthetic test fixture', 'sa', 10) result
    where result.canonical_ref = 'BG.18.997' and result.record_kind = 'original'
  ) then
    raise exception 'Verified and licensed public text was not returned by search';
  end if;

  insert into scripture.unit_texts (
    work_id, unit_id, edition_id, content_kind, language_code, text_content,
    rights_state, publication_state
  ) values (
    v_work, v_unit, v_ed2, 'original', 'sa', 'Private hidden fixture',
    'unknown', 'private'
  );

  if exists (
    select 1 from scripture.search_published_content('Private hidden fixture', 'sa', 10)
  ) then
    raise exception 'Private or unverified content leaked into public search';
  end if;

  if exists (
    select 1 from scripture.search_published_content('Synthetic test fixture', 'en', 10)
  ) then
    raise exception 'Search returned content for an unpermitted language';
  end if;

  if not scripture.permission_grant_allows(v_grant, v_ed1, 'public_display', 'sa') then
    raise exception 'Valid, current public-display permission was incorrectly denied';
  end if;
  if scripture.permission_grant_allows(v_grant, v_ed2, 'public_display', 'sa') then
    raise exception 'A grant was incorrectly accepted for a different edition';
  end if;
  if scripture.permission_grant_allows(v_grant, v_ed1, 'ai_retrieval', 'sa') then
    raise exception 'AI retrieval was incorrectly allowed by a grant that excludes it';
  end if;
  if exists (
    select 1 from scripture.search_ai_retrieval_content('Synthetic test fixture', 'sa', 10)
  ) then
    raise exception 'AI retrieval returned content without AI retrieval permission';
  end if;

  update scripture.permission_grants
  set permitted_actions = array['public_display','search_indexing','ai_retrieval'],
      ai_retrieval_allowed = true
  where id = v_grant;

  if not exists (
    select 1
    from scripture.search_ai_retrieval_content('Synthetic test fixture', 'sa', 10) result
    where result.canonical_ref = 'BG.18.997'
  ) then
    raise exception 'AI retrieval failed despite an explicit current AI permission';
  end if;
  if scripture.permission_grant_allows(v_grant, v_ed1, 'public_display', 'fr') then
    raise exception 'A language outside the grant was incorrectly allowed';
  end if;
  if scripture.permission_grant_allows(v_expired_grant, v_ed1, 'public_display', 'sa') then
    raise exception 'An expired permission grant was incorrectly accepted';
  end if;

  -- A grant for edition A must not be attachable to content for edition B.
  begin
    insert into scripture.unit_texts (
      work_id, unit_id, edition_id, content_kind, language_code, variant_label, text_content,
      permission_grant_id, rights_state, publication_state
    ) values (
      v_work, v_unit, v_ed2, 'original', 'sa', 'edition-mismatch', 'Synthetic mismatch test only',
      v_grant, 'licensed_for_use', 'private'
    );
    raise exception 'Cross-edition permission grant was incorrectly accepted';
  exception
    when foreign_key_violation then null;
  end;

  -- One canonical section cannot contain two units with the same sequence number.
  begin
    insert into scripture.units (
      work_id, section_id, canonical_ref, unit_kind, sequence_no, canonical_label
    ) values (v_work, v_section, 'BG.18.996', 'verse', 997, 'Synthetic duplicate sequence');
    raise exception 'Duplicate section sequence was incorrectly accepted';
  exception
    when unique_violation then null;
  end;
end;
$$;

rollback;
