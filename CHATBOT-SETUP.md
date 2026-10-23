# Raman Parikar chatbot

## Architecture and scope

The static GitHub Pages site loads one shared `chatbot.js` widget. It sends only the current question and selected language to the authenticated `raman-chat` Supabase Edge Function. No chat history or personal profile is stored. The function contains 14 selected scripture passages (Bhagavad-gītā, Śrīmad-Bhāgavatam, Śrī Caitanya-caritāmṛta and Nectar of Instruction) plus facts taken from the published website. It returns source text and citations from that fixed collection; AI-generated interpretation is explicitly labeled and constrained to retrieved excerpts. It does not have the complete texts or unpublished organisation material.

The function uses a small in-memory, per-isolate limiter (30 requests per 10 minutes per observed client IP). This is a best-effort abuse control, not a globally shared quota. Supabase JWT verification and exact-origin CORS are enabled. Questions and IP addresses are not logged or persisted by this code. Do not enter sensitive personal information into the chat.

## One-time provider setup for generated explanations

The function returns curated passage text and meanings without external credentials. Generated explanations require a Cloudflare account and an API token restricted to Workers AI read/inference access. Add these **server-side only** in Supabase Dashboard → Project `akfnlsyvjlxkdibfhuzy` → Edge Functions → Secrets:

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

Never add either value to GitHub, the website, or a browser. The function fails closed to curated text if the secrets are absent or the model request fails.

## Cost expectations

Supabase is currently on its Free plan. Cloudflare Workers AI Free currently includes a daily free inference allocation; usage beyond that allocation is rejected on the Free plan rather than billed. The design has no paid fallback. At low traffic this should remain ₹0, but provider quotas and plans can change. Supabase Free projects may pause after a period of inactivity. Recheck current terms before relying on a cost guarantee.

## Release checklist

1. Deploy `supabase/functions/raman-chat/index.ts` to project `akfnlsyvjlxkdibfhuzy` with JWT verification enabled.
2. Set the two Cloudflare secrets above if AI explanations are desired.
3. Publish `chatbot.js` and include `<script src="chatbot.js?v=1" defer></script>` on each HTML page.
4. Verify an OPTIONS preflight from `https://ramanparikar.github.io`, a website FAQ, a scripture question, and a rejected foreign origin. Do not submit the production Yatra form as a smoke test; it creates a real registration.

## Verified primary references

- [Cloudflare Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [Cloudflare Workers AI data usage](https://developers.cloudflare.com/workers-ai/platform/data-usage/)
- [Cloudflare REST API setup](https://developers.cloudflare.com/workers-ai/get-started/rest-api/)
- [Supabase Edge Function pricing](https://supabase.com/docs/guides/functions/pricing)
- Scripture source links are included with each passage in `index.ts` and returned to the widget.

