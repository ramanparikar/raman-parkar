import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const fn = await readFile(new URL('../supabase/functions/raman-chat/index.ts', import.meta.url), 'utf8');
const knowledge = await readFile(new URL('../supabase/functions/raman-chat/organization-knowledge.ts', import.meta.url), 'utf8');
const ui = await readFile(new URL('../chatbot.js', import.meta.url), 'utf8');

test('curated scripture collection has 19 linked references across requested works', () => {
  const refs = [...fn.matchAll(/ref:"([^"]+)"/g)].map(m => m[1]);
  assert.equal(refs.length, 19);
  assert.ok(refs.some(x => x.startsWith('Bhagavad-gītā')));
  assert.ok(refs.some(x => x.startsWith('Śrīmad-Bhāgavatam')));
  assert.ok(refs.some(x => x.startsWith('Śrī Brahma-saṁhitā')));
  assert.ok(refs.some(x => x.includes('Caitanya-caritāmṛta')));
  assert.ok(refs.some(x => x.startsWith('Nectar of Instruction')));
  assert.equal((fn.match(/url:"https:\/\/vedabase\.io\//g)||[]).length, 19);
});

test('backend locks CORS, method, input size and language', () => {
  assert.match(fn, /const ORIGIN = "https:\/\/ramanparikar\.github\.io"/);
  assert.match(fn, /req\.method !== "POST"/);
  assert.match(fn, /message\.length>1000/);
  assert.match(fn, /\['auto','en','hi'\]/);
  assert.match(fn, /rateLimited\(clientKey\)/);
  assert.match(fn, /kind:"conversation"/);
  assert.match(fn, /casualReply\(q,lang/);
  assert.match(fn, /selectWebsite\(q\)/);
  assert.match(fn, /Śrīmad-Bhāgavatam 1\.2\.6/);
  assert.match(fn, /mahamantra/);
  assert.match(fn, /query\.has\("name"\)/);
});

test('organisation FAQ is maintained separately and does not invent an events calendar', () => {
  assert.match(fn, /organization-knowledge\.ts/);
  assert.match(knowledge, /id:"join"/);
  assert.match(knowledge, /id:"kirtan"/);
  assert.match(knowledge, /id:"events"/);
  assert.match(knowledge, /do not publish a dated general events calendar/i);
});

test('frontend has no provider or service-role secret and inserts responses as text', () => {
  assert.doesNotMatch(ui, /CLOUDFLARE_API_TOKEN|service[_-]?(?:secret|credential)/i);
  assert.match(ui, /apikey:publicKey/);
  assert.match(ui, /textContent\s*=\s*text/);
  assert.match(ui, /el\.textContent\s*=\s*text/);
});

test('frontend renders citations only as safe links and distinguishes AI interpretation', () => {
  assert.match(ui, /Tabhai Prabhu/);
  assert.match(ui, /Verified scripture excerpts/);
  assert.match(ui, /vedabase\\\.io\|ramanparikar/);
  assert.match(ui, /No chat history or recordings are saved/);
  assert.match(ui, /window\.SpeechRecognition\|\|window\.webkitSpeechRecognition/);
  assert.match(ui, /SpeechSynthesisUtterance/);
  assert.match(ui, /aria-label="Pause or resume speech"/);
  assert.match(ui, /aria-label="Stop speech"/);
  assert.match(ui, /aria-label="Toggle read aloud"/);
  assert.match(ui, /let speakEnabled=false/);
});

test('mobile widget uses compact launcher and viewport-bounded chat panel', () => {
  assert.match(ui, /@media\(max-width:480px\)/);
  assert.match(ui, /width:56px;height:56px/);
  assert.match(ui, /border:2px solid #fff;border-radius:5px/);
  assert.match(ui, /height:min\(680px,calc\(100dvh - 88px\)\)/);
});

