-- Optional search indexes for Tabhai Prabhu.
-- Apply only after 001 has been reviewed and tested locally.
-- No extension is required. 'simple' avoids English-only stemming assumptions;
-- language-specific query handling belongs in the search API.

begin;

create index if not exists unit_texts_search_gin_idx
  on scripture.unit_texts using gin (
    to_tsvector('simple'::regconfig, coalesce(normalized_search_text, text_content))
  );

create index if not exists translations_search_gin_idx
  on scripture.translations using gin (
    to_tsvector('simple'::regconfig, translation_text)
  );

create index if not exists commentaries_search_gin_idx
  on scripture.commentaries using gin (
    to_tsvector('simple'::regconfig, commentary_text)
  );

create index if not exists word_meanings_search_gin_idx
  on scripture.word_meanings using gin (
    to_tsvector('simple'::regconfig, source_token || ' ' || coalesce(token_transliteration, '') || ' ' || meaning_text)
  );

create index if not exists unit_texts_language_state_idx
  on scripture.unit_texts(language_code, review_state, rights_state, publication_state);

create index if not exists translations_language_state_idx
  on scripture.translations(language_code, review_state, rights_state, publication_state);

commit;
