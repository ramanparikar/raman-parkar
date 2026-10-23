import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const fn = await readFile(new URL('../supabase/functions/raman-chat/index.ts', import.meta.url), 'utf8');
const ui = await readFile(new URL('../chatbot.js', import.meta.url), 'utf8');

test('curated scripture collection has 14 linked references across requested works', () => {
  const refs = [...fn.matchAll(/ref:"([^"]+)"/g)].map(m => m[1]);
  assert.equal(refs.length, 14);
  assert.ok(refs.some(x => x.startsWith('Bhagavad-gītā')));
  assert.ok(refs.some(x => x.startsWith('Śrīmad-Bhāgavatam')));
  assert.ok(refs.some(x => x.includes('Caitanya-caritāmṛta')));
  assert.ok(refs.some(x => x.startsWith('Nectar of Instruction')));
  assert.equal((fn.match(/url:"https:\/\/vedabase\.io\//g)||[]).length, 14);
});

test('backend locks CORS, method, input size and language', () => {
  assert.match(fn, /const ORIGIN = "https:\/\/ramanparikar\.github\.io"/);
  assert.match(fn, /req\.method !== "POST"/);
  assert.match(fn, /message\.length>1000/);
  assert.match(fn, /\['en','hi'\]/);
  assert.match(fn, /rateLimited\(clientKey\)/);
});

test('frontend has no provider or service-role secret and inserts responses as text', () => {
  assert.doesNotMatch(ui, /CLOUDFLARE_API_TOKEN|service[_-]?(?:secret|credential)/i);
  assert.match(ui, /apikey:publicKey/);
  assert.match(ui, /textContent\s*=\s*text/);
  assert.match(ui, /el\.textContent\s*=\s*text/);
});

test('frontend renders citations only as safe links and distinguishes AI interpretation', () => {
  assert.match(ui, /AI interpretation/);
  assert.match(ui, /Verified scripture excerpts/);
  assert.match(ui, /vedabase\\\.io\|ramanparikar/);
  assert.match(ui, /No chat history is saved/);
});

