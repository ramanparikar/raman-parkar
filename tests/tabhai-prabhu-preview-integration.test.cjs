"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");

const html = fs.readFileSync("tabhai-prabhu-preview.html", "utf8");
const app = fs.readFileSync("tabhai-prabhu-preview.js", "utf8");

test("preview loads shared reference utility before the interface script", () => {
  const utilityAt = html.indexOf("tabhai-prabhu-reference-utils.js");
  const appAt = html.indexOf("tabhai-prabhu-preview.js");
  assert.notEqual(utilityAt, -1);
  assert.notEqual(appAt, -1);
  assert.ok(utilityAt < appAt);
});

test("preview exposes accessible live regions for index and reference search", () => {
  assert.match(html, /id="tp-unit-list"[^>]*aria-live="polite"/);
  assert.match(html, /id="tp-search-result"[^>]*aria-live="polite"/);
  assert.match(html, /id="tp-result"[^>]*aria-live="polite"/);
});

test("preview has all three work selectors and reference controls", () => {
  for (const work of ["BG", "SB", "CC"]) assert.match(html, new RegExp('data-work="' + work + '"'));
  for (const id of ["tp-section", "tp-chapter", "tp-unit", "tp-ref", "tp-copy", "tp-search-form"]) {
    assert.match(html, new RegExp('id="' + id + '"'));
  }
});

test("interface delegates reference construction to the shared utility", () => {
  assert.match(app, /window\.TabhaiPrabhuRefs\.chapterCounts\(\)/);
  assert.match(app, /window\.TabhaiPrabhuRefs\.provisionalChapterRefs\(chapterNo\)/);
  assert.match(app, /window\.TabhaiPrabhuRefs\?\.parse\(value\)/);
});

test("non-Gita works do not fabricate unit inventories", () => {
  assert.match(app, /if\(selected!==\"BG\"\)/);
  assert.match(app, /No chapter\/unit inventory is displayed until an exact edition is selected and checked/);
});
