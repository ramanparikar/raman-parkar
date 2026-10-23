# Tabhai Prabhu chatbot

## What it uses

The static GitHub Pages site loads the shared `chatbot.js` widget on each current page. It calls the `raman-chat` Supabase Edge Function with the current question and language preference. The browser stores no chat history or voice recordings. Voice input/output use browser speech APIs when supported.

The function retrieves from a curated set of 19 checked passages rather than a full-text archive. The collection covers Bhagavad-gītā, Śrīmad-Bhāgavatam, Śrī Caitanya-caritāmṛta, Śrī Brahma-saṁhitā and Nectar of Instruction. Verse text and citations come from Vedabase links included with each record. `organization-knowledge.ts` is the editable English/Hindi FAQ source; update it when public website details, event dates or policies change. Only publish verified information.

Greetings, thanks and casual conversation work without scripture citations. If provider credentials are configured, these replies and source-grounded spiritual explanations use Cloudflare Workers AI. Without credentials, casual replies use a short local response and spiritual answers still return matched verses with curated meanings. The function never invents a verse or citation and does not claim to retrieve entire books.

## Required one-time setup for AI-generated replies

The active Edge Function currently has no Cloudflare credentials configured, so AI-generated wording cannot run. To enable it, create a Cloudflare account and a token limited to Workers AI inference, then add these secrets in Supabase Dashboard → Project `akfnlsyvjlxkdibfhuzy` → Edge Functions → Secrets:

- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

Keep both values server-side. Never add them to this repository or browser code. No paid plan or paid fallback is enabled.

## Cost and limitations

GitHub Pages and Supabase are currently used on free service tiers. Cloudflare Workers AI's Free tier currently provides up to 10,000 neurons per day; requests stop when that allocation is exhausted. The selected model is listed as available on Free tier. There is no automatic paid upgrade or fallback. Current plans and limits can change, so verify provider terms before relying on the ₹0–₹100/year target. Supabase Free projects may pause during extended inactivity. Browser speech recognition availability and voice selection vary by browser, operating system and installed voices. Typing remains available.

## Verification and deployment

Deploy `supabase/functions/raman-chat/index.ts` plus `organization-knowledge.ts` with JWT verification enabled. Confirm exact-origin CORS from `https://ramanparikar.github.io`. Then publish the widget and the script reference on all HTML pages. A live Yatra form submission creates a real attendee record, so do not use the production form as a smoke test without arranging a clearly identified test record with the organisers.

## Primary references

- [Cloudflare Workers AI pricing and quotas](https://developers.cloudflare.com/workers-ai/platform/pricing/)
- [Cloudflare Workers AI data usage](https://developers.cloudflare.com/workers-ai/platform/data-usage/)
- [Cloudflare Workers AI REST API](https://developers.cloudflare.com/workers-ai/get-started/rest-api/)
- [Supabase Edge Function pricing](https://supabase.com/docs/guides/functions/pricing)
- Scripture links are included with each passage in `index.ts`.

