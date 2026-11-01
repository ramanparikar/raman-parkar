# Tabhai Prabhu — Future Server API Contract

**Status:** design only. No Edge Function is deployed and no production project is changed.

## Security boundary

- Browser code must never connect directly to the private `scripture` schema.
- Browser code must never contain a Supabase service-role key or database credentials.
- A future server-side endpoint must authenticate/validate requests, apply rate limits and call only the approved database functions.
- The endpoint must not return full copyrighted passages unless the exact edition grant explicitly permits that output.
- Search-indexing permission is not AI-retrieval permission. The two database functions are intentionally separate.
- Every returned item must preserve `canonical_ref`, `edition_id` and `source_id` so the UI can cite the exact source and edition.
- Do not deploy this contract to the existing production Supabase project without separate approval.

## Endpoint A — public scripture search

**Suggested route:** `POST /scripture/search`

Request:

```json
{
  "query": "dharma",
  "language": "en",
  "limit": 10
}
```

Server behaviour:
1. Validate non-empty query, supported language and a limit from 1 to 20.
2. Call `scripture.search_published_content(query, language, limit)`.
3. Resolve each returned `source_id` to a bibliographic citation.
4. Return only the bounded snippets supplied by the database function.
5. Never bypass the database's verified/published and current rights checks.

Response shape:

```json
{
  "results": [
    {
      "canonical_ref": "BG.02.047",
      "edition_id": "uuid",
      "source_id": "uuid",
      "record_kind": "original",
      "language": "sa",
      "snippet": "bounded excerpt",
      "citation": {
        "work": "Bhagavad-gita",
        "edition": "verified edition title",
        "source": "registered source title"
      }
    }
  ]
}
```

The identifiers and sample values above illustrate the shape only; they are not actual database records.

## Endpoint B — AI retrieval

**Suggested route:** `POST /scripture/ai-retrieval`

Request:

```json
{
  "query": "What is the meaning of duty?",
  "language": "en",
  "limit": 5
}
```

Server behaviour:
1. Validate request size, language and a limit from 1 to 10.
2. Call `scripture.search_ai_retrieval_content(query, language, limit)`; do not call the public-search function as a substitute.
3. Pass only returned, bounded excerpts to the model.
4. Require answers to cite canonical reference, edition and source.
5. If no permitted source is returned, say that the knowledge base has no authorised material for the query; do not silently fall back to scraped or unlicensed material.
6. Keep retrieved passages out of application logs unless a reviewed retention policy explicitly permits them.

Response shape:

```json
{
  "answer": "Generated answer with source references.",
  "citations": [
    {
      "canonical_ref": "BG.02.047",
      "edition_id": "uuid",
      "source_id": "uuid"
    }
  ]
}
```

## Required endpoint controls

- Rate limiting by IP and authenticated account where applicable.
- Request and response size caps.
- Query length cap and strict input validation.
- No SQL string concatenation; use parameterised calls.
- No direct table access from browser roles.
- No service-role secret in client-side HTML/JavaScript.
- Citation rendering must resolve the exact edition/source, not a generic work title.
- Expired/revoked permission must take effect on the next request.
- Logs must not retain copyrighted snippets or personal query content beyond the approved retention period.
- Add automated tests for missing rights, expired rights, wrong language, private content and wrong-edition grants.

## Not implemented by this document

No Supabase function, API route, frontend integration, authentication change, production migration, deployment or AI-provider configuration is created by this contract.
