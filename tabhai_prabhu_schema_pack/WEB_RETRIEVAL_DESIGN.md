# Tabhai Prabhu — Web-grounded scripture retrieval (Option A)

Status: approved product direction; development design only. This document does not authorise a production deployment, a live database change, or reproduction of protected source material.

## Product decision

Use web-grounded retrieval as the primary way Tabhai Prabhu discovers scripture references and source material. Do not build a complete mirror of copyrighted books as a prerequisite for answering questions.

A user may ask, for example, "Explain Bhagavad-gita 10.10." The system should discover relevant sources, identify the exact edition/source, retrieve only material that the source's terms and applicable law permit, answer with attribution, and provide a direct source link.

## Critical distinction

Public accessibility is not a licence to copy. Search-result visibility, a publicly accessible URL, or a browser being able to fetch a page does not by itself grant permission to reproduce the page's text, translations, purports, illustrations, or other protected content.

Until the relevant rights are confirmed:
- Do not crawl, bulk-fetch, scrape, mirror, or systematically extract Vedabase/BBT content.
- Do not reproduce BBT translations, purports, editorial notes, scans, or other protected material in answers merely because a URL is public.
- It is acceptable to provide a source link and bibliographic metadata where lawfully obtained.
- Use complete verse text or translations only from sources whose licence clearly permits the specific display and retrieval use, or after written permission.
- Ancient underlying Sanskrit works may have public-domain status, but a modern edition, translation, transliteration, commentary, or typesetting may have separate rights. Assess each layer independently.

## User experience

1. Accept a natural-language question or a precise reference.
2. Parse a possible reference (work, chapter/canto, verse).
3. Search trusted source discovery endpoints.
4. Rank sources by authority, edition clarity, language, relevance, and freshness.
5. Open or retrieve a source only when its terms, technical access rules, and applicable law permit it.
6. Extract the minimum relevant material needed for the answer; do not retain full page text.
7. Generate an explanation grounded in the retrieved material, distinguishing quotation, paraphrase, and the assistant's own explanation.
8. Show source title, publisher/site, edition where known, direct URL, and access date.
9. If no source permits reproduction, show a source link and explain that the text cannot be reproduced in this response; do not fabricate a verse or citation.

## Source policy and records

Maintain a small source registry with:
- canonical source URL and publisher/rights-holder;
- work and edition identifiers, where known;
- language and content type (original text, transliteration, translation, commentary, metadata);
- access method and terms URL;
- rights basis/status: public-domain evidence, explicit licence, written permission, link-only, or blocked/pending;
- allowed actions: discover, link, retrieve, quote, display, index, embeddings, AI retrieval, redistribution;
- evidence date, reviewer, restrictions, and review/expiry date.

Default to deny for unknown rights. A source marked link-only may be cited and linked but its protected text must not be copied into the answer. Permission for one content type or action must not be inferred to cover another.

## Retrieval architecture (future implementation)

Keep provider-specific search behind a server-side adapter. The browser must never contain search-provider API keys.

Suggested request:
- query: user question or reference;
- language: requested response language;
- work_hint: optional BG/SB/CC/etc.;
- reference_hint: optional canonical reference.

Suggested response:
- answer: concise source-grounded explanation;
- sources[]: title, publisher, edition, URL, retrieved_at, rights_status;
- passages[]: only permitted excerpts, with content type, language, reference and source;
- limitations[]: edition ambiguity, unavailable source, or rights restriction.

The server must:
- keep credentials in server-side secrets;
- enforce an allowlist/denylist and source-specific rights policy;
- use timeouts, response-size limits, rate limits, and safe URL validation;
- block private-network, localhost, file, and non-HTTP(S) targets to prevent SSRF;
- reject paywall circumvention, login bypass, CAPTCHA bypass, and access-control evasion;
- avoid persistent storage of retrieved page text by default;
- log source metadata and request outcomes, not full copyrighted page bodies;
- treat retrieved webpages as untrusted data, never as system instructions;
- return citations with every factual scripture-source claim;
- fail closed if rights metadata is missing or expired.

No search vendor or paid service is selected by this design. Prefer a genuinely free, documented search API or a user-clicked search link until cost, quotas, terms, and technical access are verified. Do not silently introduce a paid dependency.

## Existing project boundaries

- Implement future work only on the tabhai-prabhu-scripture-db development branch and existing draft PR.
- Do not merge to main.
- Do not deploy or modify production.
- Do not change the existing Yatra registration system, production chatbot, production Supabase project, or production CORS configuration without separate explicit approval.
- Do not create a paid Supabase branch, paid API dependency, or paid hosting dependency.
- Keep the current reference/edition validators as metadata-quality tools; they do not establish copyright permission or textual accuracy.

## Acceptance criteria for a first web-retrieval prototype

- A precise reference query can return a list of source links without copying restricted text.
- Every displayed quotation has a source and a rights basis that explicitly permits display.
- Link-only sources produce links, not copied passages.
- The interface identifies the edition when the source provides it and flags edition ambiguity otherwise.
- The system never invents a verse, translation, purport, URL, or edition.
- No search-provider key is exposed in browser JavaScript.
- No retrieved full page or protected text is persisted.
- Tests cover blocked sources, expired permissions, missing rights metadata, link-only results, allowed short excerpts, malicious page instructions, and invalid URLs.
- Existing chatbot and Yatra tests continue to pass unchanged.
