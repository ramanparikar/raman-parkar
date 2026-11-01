"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const refs = require("../tabhai-prabhu-reference-utils.js");

class FakeElement {
  constructor(id = "") {
    this.id = id; this.value = ""; this.textContent = ""; this.dataset = {};
    this.hidden = false; this.max = ""; this.children = []; this.listeners = {};
    this.classList = { toggle() {} };
  }
  addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); }
  dispatch(name, event = {}) { for (const callback of this.listeners[name] || []) callback(event); }
  replaceChildren() { this.children = []; this.value = ""; }
  append(child) { this.children.push(child); if (this.value === "" && child.value !== undefined) this.value = String(child.value); }
  scrollIntoView() {}
  click() { this.dispatch("click", {}); }
}

function createPreview() {
  const ids = ["tp-unit-list","tp-index-note","tp-index-count","tp-unit-label","tp-section","tp-chapter","tp-chapter-field","tp-unit","tp-ref","tp-description","tp-open","tp-copy","tp-search-form","tp-query","tp-search-result","tp-result"];
  const elements = Object.fromEntries(ids.map(id => [id, new FakeElement(id)]));
  const workButtons = ["BG","SB","CC"].map(work => { const el = new FakeElement(); el.dataset.work = work; return el; });
  elements["tp-unit"].value = "1";
  elements["tp-query"].value = "";
  const document = {
    querySelector(selector) { return elements[selector.replace(/^#/, "")]; },
    querySelectorAll(selector) { return selector === "[data-work]" ? workButtons : []; },
    createElement() { return new FakeElement(); }
  };
  const window = { TabhaiPrabhuRefs: refs };
  vm.runInNewContext(fs.readFileSync("tabhai-prabhu-preview.js", "utf8"), {
    window, document, navigator: { clipboard: { writeText: async value => { window.copied = value; } } }
  });
  return { elements, workButtons, window };
}

test("Gita chapter index updates and selecting a reference fills the locator", () => {
  const { elements } = createPreview();
  assert.equal(elements["tp-unit-list"].children.length, 47);
  elements["tp-section"].value = "2";
  elements["tp-section"].dispatch("change");
  assert.equal(elements["tp-unit-list"].children.length, 72);
  elements["tp-unit-list"].children[71].click();
  assert.equal(Number(elements["tp-unit"].value), 72);
  assert.equal(elements["tp-ref"].textContent, "BG.02.072");
});

test("Bhagavatam and Caitanya-caritamrita avoid invented unit inventories", () => {
  const { elements, workButtons } = createPreview();
  workButtons[1].click();
  assert.equal(elements["tp-unit-list"].children.length, 0);
  assert.match(elements["tp-index-note"].textContent, /No chapter\/unit inventory/);
  assert.equal(elements["tp-ref"].textContent, "SB.01.01.001");
  workButtons[2].click();
  assert.equal(elements["tp-unit-list"].children.length, 0);
  assert.equal(elements["tp-ref"].textContent, "CC.ADI.01.001");
});

test("reference search reports provisional baseline limits without claiming verification", () => {
  const { elements } = createPreview();
  elements["tp-query"].value = "BG.01.048";
  let prevented = false;
  elements["tp-search-form"].dispatch("submit", { preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  assert.match(elements["tp-search-result"].textContent, /outside the provisional chapter-count baseline/);
  assert.match(elements["tp-search-result"].textContent, /not proof of edition-level existence/);
});

test("copy control copies the currently displayed canonical reference", async () => {
  const { elements, window } = createPreview();
  elements["tp-copy"].click();
  await Promise.resolve();
  assert.equal(window.copied, "BG.01.001");
});
