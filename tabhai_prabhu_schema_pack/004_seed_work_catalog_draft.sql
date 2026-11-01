-- Safe metadata-only seed for LOCAL development.
-- Contains work titles only; no scripture text, translations, commentary, or scans.

insert into scripture.works (code, canonical_title, alternate_titles, work_language, description)
values
  ('BG', 'Bhagavad-gita', array['Bhagavad-gita As It Is'], 'sa',
   'Primary work record. Edition metadata and expected verse inventory must be added from the selected, documented edition.'),
  ('SB', 'Srimad-Bhagavatam', array['Bhagavata Purana'], 'sa',
   'Primary work record. Canto, chapter and verse inventory must be derived from the selected edition; do not assume a universal total.'),
  ('CC', 'Sri Caitanya-caritamrita', array['Caitanya-caritamrita'], 'bn',
   'Primary work record. Adi, Madhya and Antya textual units must be inventoried from the selected edition, including non-verse units.')
on conflict (code) do nothing;
