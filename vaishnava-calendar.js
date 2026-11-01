(() => {
  "use strict";

  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const startKey = "2026-01-06";
  const endKey = "2027-04-13";
  const days = new Map();
  const dateLabels = new Intl.DateTimeFormat("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const monthLabels = new Intl.DateTimeFormat("en-IN", { month: "long", year: "numeric", timeZone: "UTC" });
  const $ = selector => document.querySelector(selector);

  const esc = value => String(value ?? "").replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  })[character]);

  const keyFor = (year, month, day) => `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  const dateFor = key => new Date(`${key}T00:00:00Z`);
  const plusOneDay = key => {
    const date = dateFor(key);
    date.setUTCDate(date.getUTCDate() + 1);
    return keyFor(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
  };

  function todayInDelhi() {
    const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
    const part = type => parts.find(value => value.type === type).value;
    return `${part("year")}-${part("month")}-${part("day")}`;
  }

  function decodeIcsText(value) {
    const unescaped = value
      .replace(/\\[nN]/g, " ")
      .replace(/\\,/g, ",")
      .replace(/\\;/g, ";")
      .replace(/\\\\/g, "\\");
    const plain = unescaped.replace(/<\/?[^>]*>/g, " ").replace(/\s+/g, " ").trim();
    const textarea = document.createElement("textarea");
    textarea.innerHTML = plain;
    return textarea.value.replace(/\s+/g, " ").trim();
  }

  function parseIcs(text) {
    const unfolded = text.replace(/^\uFEFF/, "").replace(/\r?\n[ \t]/g, "");
    const events = [];
    for (const block of unfolded.split(/BEGIN:VEVENT\s*/i).slice(1)) {
      const body = block.split(/END:VEVENT/i, 1)[0];
      const dateMatch = body.match(/^DTSTART(?:;[^:]*)?:(\d{4})(\d{2})(\d{2})/im);
      const summaryLine = body.split(/\r?\n/).find(line => /^SUMMARY:/i.test(line));
      if (!dateMatch || !summaryLine) continue;
      events.push({
        key: `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]}`,
        summary: decodeIcsText(summaryLine.slice(summaryLine.indexOf(":") + 1))
      });
    }
    return events;
  }

  function dayFor(key) {
    if (!days.has(key)) days.set(key, { key, events: [], fastings: [], paranas: [] });
    return days.get(key);
  }

  function removeNabadwipLocalFastAndParan(summary) {
    return summary
      .replace(/\bNo fast today\b[^.]*\.?/gi, " ")
      .replace(/\b(?:Fast|Fasting)\b[\s\S]*?\(in Nabadwip\)\.?/gi, " ")
      .replace(/\bParan\b[\s\S]*?\(in Nabadwip\)\.?/gi, " ")
      .replace(/\s*\.\s*\.\s*/g, ". ")
      .replace(/\s+([,.;])/g, "$1")
      .replace(/^[\s.;,]+|[\s.;,]+$/g, "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function localFastNames(summary) {
    const specific = [...summary.matchAll(/\bFast(?:ing)?\s+for\s+([^.]*)\(in Delhi\)/gi)]
      .map(match => match[1].replace(/[.\s]+$/g, "").trim())
      .filter(Boolean);
    const genericMatch = /\bFast(?:ing)?\s*\(in Delhi\)/i.exec(summary);
    if (!genericMatch) return specific;
    const prefix = summary.slice(0, genericMatch.index);
    const candidates = prefix.split(/(?<=\.)\s*/).map(value => value.replace(/[.\s]+$/g, "").trim()).filter(Boolean);
    const named = [...candidates].reverse().find(value => /\b(?:Ekadashi|Mahadvadashi)\b/i.test(value));
    return [...specific, named || candidates.at(-1) || "Fasting observance"];
  }

  function localParanaDetails(summary) {
    const match = summary.match(/\bParan\b([\s\S]*?)\(in Delhi\)/i);
    return match ? match[1].replace(/[.\s]+$/g, "").trim() : "";
  }

  function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function removeDuplicateFastTitle(name, fastName) {
    const title = new RegExp(`(?:^|\\.\\s*)${escapeRegExp(fastName)}\\.?`, "i");
    return name.replace(title, " ").replace(/\s*\.\s*\./g, ". ").replace(/^[\s.;,]+|[\s.;,]+$/g, "").replace(/\s+/g, " ").trim();
  }

  function splitObservances(summary) {
    const protectedInitials = summary.replace(/\b(?:[A-Z]\.){1,4}/g, initials => initials.replace(/\./g, "\uE000"));
    return protectedInitials
      .split(/(?<=[.!?])\s+(?=[A-Z])/)
      .map(item => item.replace(/\uE000/g, ".").replace(/^[\s.;]+|[\s.;]+$/g, "").trim())
      .filter(Boolean);
  }

  function gaurabdaYear(key) {
    if (key < "2026-03-04") return "540";
    if (key < "2027-03-23") return "541";
    return "542";
  }

  function insideSourceSpan(key) {
    return key >= startKey && key <= endKey;
  }

  function renderDay(key) {
    const day = days.get(key) || { key, events: [], fastings: [], paranas: [] };
    const isCovered = insideSourceSpan(key);
    $("#selected-date-title").textContent = dateLabels.format(dateFor(key));
    $("#selected-date-masa").textContent = `Gaurabda ${gaurabdaYear(key)} · Delhi local calendar`;

    const facts = [
      ["Gaurabda year", gaurabdaYear(key)],
      ["Delhi timezone", "Asia/Kolkata · IST"],
      ["Source span", isCovered ? "Published dates" : "Outside source span"]
    ];
    $("#selected-date-facts").innerHTML = facts.map(([label, value]) => `<div class="calendar-fact"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join("");

    const entries = [];
    for (const item of day.fastings) entries.push(`<li class="fasting"><strong>Delhi fast:</strong> ${esc(item.name)}</li>`);
    for (const item of day.paranas) entries.push(`<li class="parana"><strong>Parana:</strong> ${esc(item.details)} IST · Delhi local time</li>`);
    for (const item of day.events) entries.push(`<li class="${esc(item.kind)}">${esc(item.name)}</li>`);

    const emptyNote = isCovered
      ? "No observance is listed for this date in the published SCSMath sources."
      : "This day is outside the dated observances in the published SCSMath calendar files.";
    $("#selected-date-observances").innerHTML = entries.length
      ? `<ul class="calendar-observance-list">${entries.join("")}</ul>`
      : `<p class="calendar-empty-note">${emptyNote}</p>`;

    document.querySelectorAll(".calendar-day[data-date]").forEach(button => {
      const active = button.dataset.date === key;
      button.classList.toggle("is-selected", active);
      button.setAttribute("aria-pressed", String(active));
    });
    renderGaurabda(key);
  }

  let viewYear = 2026;
  let viewMonth = 0;
  let selectedKey = "";
  let activeFilter = "all";

  function renderGaurabda(selectedKey) {
    const years = [...new Set(Array.from({ length: new Date(Date.UTC(viewYear, viewMonth + 1, 0)).getUTCDate() }, (_, index) =>
      gaurabdaYear(keyFor(viewYear, viewMonth, index + 1))))];
    $("#current-gaurabda-month").textContent = `Gaurabda ${gaurabdaYear(selectedKey)}`;
    const yearText = years.length > 1 ? `Gaurabda ${years.join(" and ")}` : `Gaurabda ${years[0]}`;
    $("#month-transition-note").textContent = `${monthNames[viewMonth]} ${viewYear} falls in ${yearText}. Masa names are listed from the SCSMath calendar; the source ICS does not assign a masa to every date.`;
  }

  function renderMonth() {
    const first = new Date(Date.UTC(viewYear, viewMonth, 1));
    const length = new Date(Date.UTC(viewYear, viewMonth + 1, 0)).getUTCDate();
    const start = first.getUTCDay();
    $("#month-title").textContent = monthLabels.format(first);
    const cells = [];
    for (let i = 0; i < start; i++) cells.push(`<span class="calendar-day calendar-day--empty" aria-hidden="true"></span>`);

    for (let number = 1; number <= length; number++) {
      const key = keyFor(viewYear, viewMonth, number);
      const day = days.get(key) || { events: [], fastings: [], paranas: [] };
      const types = new Set(day.events.map(item => item.kind));
      if (day.fastings.length) types.add("fasting");
      if (day.paranas.length) types.add("parana");
      const typeNames = ["fasting", "parana", "festival", "acharya"].filter(type => types.has(type));
      const badge = day.fastings[0]?.name || day.paranas[0]?.details || day.events[0]?.name || "";
      const sourceClass = insideSourceSpan(key) ? "" : " calendar-day--outside-source";
      const ariaParts = [dateLabels.format(dateFor(key))];
      if (day.fastings.length) ariaParts.push(`Delhi fast for ${day.fastings.map(item => item.name).join(", ")}`);
      if (day.paranas.length) ariaParts.push(`Delhi Parana ${day.paranas.map(item => item.details).join(", ")} IST`);
      for (const event of day.events) ariaParts.push(event.name);
      if (!insideSourceSpan(key)) ariaParts.push("outside published source span");
      cells.push(`<button class="calendar-day${sourceClass}${selectedKey === key ? " is-selected" : ""}" type="button" role="gridcell" data-date="${key}" aria-label="${esc(ariaParts.join(". "))}" aria-pressed="${selectedKey === key}"><span class="calendar-day__number">${number}</span>${badge ? `<span class="calendar-day__label ${typeNames[0] || "festival"}">${esc(badge)}</span>` : ""}${typeNames.length ? `<span class="calendar-day__dots" aria-hidden="true">${typeNames.map(type => `<i class="${type}"></i>`).join("")}</span>` : ""}</button>`);
    }
    $("#calendar-days").innerHTML = cells.join("");
    $("#calendar-days").querySelectorAll("button[data-date]").forEach(button => button.addEventListener("click", () => {
      selectedKey = button.dataset.date;
      renderMonth();
      renderDay(selectedKey);
    }));

    const atFirstMonth = viewYear === 2026 && viewMonth === 0;
    const atLastMonth = viewYear === 2027 && viewMonth === 3;
    $("#previous-month").disabled = atFirstMonth;
    $("#next-month").disabled = atLastMonth;
    renderGaurabda(selectedKey || keyFor(viewYear, viewMonth, 1));
  }

  function upcomingItems() {
    const today = todayInDelhi();
    const items = [];
    for (const day of [...days.values()].filter(item => item.key >= today && insideSourceSpan(item.key)).sort((a, b) => a.key.localeCompare(b.key))) {
      for (const fast of day.fastings) {
        const nextDay = days.get(plusOneDay(day.key));
        items.push({
          key: day.key,
          kind: "fasting",
          name: fast.name,
          paranaDate: nextDay?.paranas.length ? nextDay.key : "",
          parana: nextDay?.paranas[0]?.details || ""
        });
      }
      for (const parana of day.paranas) items.push({ key: day.key, kind: "parana", name: parana.details });
      for (const event of day.events) items.push({ key: day.key, kind: event.kind, name: event.name });
    }
    return items.sort((a, b) => a.key.localeCompare(b.key));
  }

  function renderUpcoming(filter = "all") {
    const allItems = upcomingItems();
    const filtered = allItems.filter(item => {
      if (filter === "fasting") return item.kind === "fasting" || item.kind === "parana";
      return filter === "all" || item.kind === filter;
    });
    const shown = filtered.slice(0, filter === "fasting" ? 90 : 42);
    $("#upcoming-status").textContent = shown.length
      ? `Showing ${shown.length}${filtered.length > shown.length ? ` of ${filtered.length}` : ""} published items through 13 April 2027.`
      : "No matching future observances remain in the published SCSMath source span.";

    $("#upcoming-observances").innerHTML = shown.map(item => {
      const date = dateLabels.format(dateFor(item.key));
      const tag = item.kind === "fasting" ? "Delhi fast" : item.kind === "parana" ? "Delhi Parana" : item.kind === "acharya" ? "Acharya day" : "Festival";
      const details = item.kind === "fasting"
        ? item.parana
          ? `<p><strong>Parana · ${esc(dateLabels.format(dateFor(item.paranaDate)))}:</strong> ${esc(item.parana)} IST · Delhi</p>`
          : `<p>Parana timing is not listed in the included Delhi supplement.</p>`
        : item.kind === "parana"
          ? `<p><strong>Delhi local time:</strong> ${esc(item.name)} IST</p>`
          : "";
      const title = item.kind === "parana" ? "Breaking fast" : item.name;
      return `<article class="upcoming-card"><span class="upcoming-card__date">${esc(date)}</span><span class="upcoming-card__tag ${esc(item.kind)}">${tag}</span><h3>${esc(title)}</h3>${details}</article>`;
    }).join("");
  }

  function moveMonth(delta) {
    const next = new Date(Date.UTC(viewYear, viewMonth + delta, 1));
    viewYear = next.getUTCFullYear();
    viewMonth = next.getUTCMonth();
    selectedKey = keyFor(viewYear, viewMonth, 1);
    renderMonth();
    renderDay(selectedKey);
  }

  async function fetchCalendar(path) {
    const response = await fetch(path, { cache: "no-cache" });
    if (!response.ok) throw new Error(`Could not load ${path}.`);
    return parseIcs(await response.text());
  }

  async function loadSources() {
    const [nabadwipEvents, delhiEvents] = await Promise.all([
      fetchCalendar("calendar-data/scsmath-nabadwip-observances-2026-2027.ics"),
      fetchCalendar("calendar-data/scsmath-delhi-2026-2027.ics")
    ]);
    if (!nabadwipEvents.length || !delhiEvents.length) throw new Error("A calendar source file did not contain dated events.");

    for (const event of nabadwipEvents) {
      const name = removeNabadwipLocalFastAndParan(event.summary);
      if (!name) continue;
      dayFor(event.key).events.push({
        name,
        kind: /\b(?:Appearance|Disappearance)\b/i.test(name) ? "acharya" : "festival"
      });
    }

    for (const event of delhiEvents) {
      const day = dayFor(event.key);
      for (const name of localFastNames(event.summary)) day.fastings.push({ name });
      const details = localParanaDetails(event.summary);
      if (details) day.paranas.push({ details });
    }

    for (const key of days.keys()) {
      const day = days.get(key);
      for (const fast of day.fastings) {
        day.events = day.events.map(event => ({ ...event, name: removeDuplicateFastTitle(event.name, fast.name) })).filter(event => event.name);
      }
      day.events = day.events.flatMap(event => splitObservances(event.name).map(name => ({
        name,
        kind: /\b(?:Appearance|Disappearance)\b/i.test(name) ? "acharya" : "festival"
      })));
      day.events.sort((a, b) => a.name.localeCompare(b.name));
    }
  }

  async function start() {
    const status = $("#calendar-status");
    const today = todayInDelhi();
    selectedKey = today >= startKey && today <= endKey ? today : startKey;
    const selectedDate = dateFor(selectedKey);
    viewYear = selectedDate.getUTCFullYear();
    viewMonth = selectedDate.getUTCMonth();

    document.querySelectorAll(".calendar-filter").forEach(button => button.addEventListener("click", () => {
      activeFilter = button.dataset.filter;
      document.querySelectorAll(".calendar-filter").forEach(item => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      renderUpcoming(activeFilter);
    }));

    try {
      await loadSources();
      status.textContent = "SCSMath observances loaded · Delhi fast and Parana details shown in IST.";
      status.classList.add("is-ready");
    } catch (error) {
      status.textContent = "Calendar source files could not load. The date grid remains available; check the source links below.";
      status.classList.add("is-error");
      console.error(error);
    }

    renderMonth();
    renderDay(selectedKey);
    renderUpcoming(activeFilter);
    $("#previous-month").addEventListener("click", () => {
      if (!(viewYear === 2026 && viewMonth === 0)) moveMonth(-1);
    });
    $("#next-month").addEventListener("click", () => {
      if (!(viewYear === 2027 && viewMonth === 3)) moveMonth(1);
    });
    const feed = new URL("calendar-data/raman-parikar-panchanga-2026-2027.ics", window.location.href);
    $("#calendar-feed-url").value = feed.href;
    $("#copy-feed-url").addEventListener("click", async () => {
      const copyStatus = $("#copy-status");
      try {
        await navigator.clipboard.writeText(feed.href);
        copyStatus.textContent = "Feed URL copied.";
      } catch {
        $("#calendar-feed-url").select();
        copyStatus.textContent = "Select and copy the feed URL.";
      }
    });
  }

  start();
})();
