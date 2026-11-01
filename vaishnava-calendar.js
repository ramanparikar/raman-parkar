(() => {
  "use strict";

  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const days = new Map();
  const dateLabels = new Intl.DateTimeFormat("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
  const monthLabels = new Intl.DateTimeFormat("en-IN", { month: "long", year: "numeric", timeZone: "UTC" });
  const $ = selector => document.querySelector(selector);

  const esc = value => String(value ?? "").replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  })[character]);

  const keyFor = (year, month, day) => `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  const dateFor = key => new Date(`${key}T00:00:00Z`);
  const todayInDelhi = () => {
    const parts = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(new Date());
    const part = type => parts.find(value => value.type === type).value;
    return `${part("year")}-${part("month")}-${part("day")}`;
  };

  function parseSource(text) {
    let currentMasa = "";
    let currentGaurabda = "";
    let currentDay = null;

    for (const line of text.replace(/^\uFEFF/, "").split(/\r?\n/)) {
      const heading = line.match(/^\s*(.*?)\s+Masa,\s*Gaurabda\s+(\d+)/);
      if (heading) {
        currentMasa = heading[1].trim();
        currentGaurabda = heading[2];
      }

      const row = line.match(/^\s*(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})\s+\w{2}\s+(.+)$/);
      if (row) {
        const [, dayNumber, monthName, year, remainder] = row;
        const tithiParts = remainder.match(/^(.*?)\s+([KG])\s+([\s\S]*?)(?:\s+\*)?\s*$/);
        if (!tithiParts) continue;
        const key = keyFor(Number(year), months.indexOf(monthName), Number(dayNumber));
        currentDay = {
          key,
          year: Number(year),
          month: months.indexOf(monthName),
          day: Number(dayNumber),
          tithi: tithiParts[1].trim(),
          paksa: tithiParts[2] === "K" ? "Krishna" : "Gaura",
          paksaCode: tithiParts[2],
          nakshatra: tithiParts[3].trim().replace(/\s+\*$/, "").trim(),
          masa: currentMasa,
          gaurabda: currentGaurabda,
          events: [],
          fastName: "",
          parana: ""
        };
        days.set(key, currentDay);
        continue;
      }

      if (!currentDay) continue;
      const event = line.trim();
      if (!event || /^DATE\b/.test(event) || /^-+/.test(event) || /^Delhi \[India\]/.test(event) || /^GCal\b/.test(event)) continue;
      if (event.startsWith("Fasting for ")) {
        currentDay.fastName = event.slice("Fasting for ".length).trim();
        currentDay.events.push({ name: currentDay.fastName, kind: "fasting" });
      } else if (event.startsWith("Break fast ")) {
        currentDay.parana = event.slice("Break fast ".length).replace(/\s+LT\s*$/, "").trim();
      } else if (/^Fasting is done\.?$/i.test(event)) {
        continue;
      } else if (/^\((?:Fast|Fasting)\b/i.test(event)) {
        currentDay.events.push({ name: `Fasting note: ${event.slice(1, -1).trim()}`, kind: "fasting-note" });
      } else {
        const kind = /\b(Appearance|Disappearance)\b/i.test(event) ? "acharya" : "festival";
        currentDay.events.push({ name: event, kind });
      }
    }
  }

  function currentDayKey() {
    const today = todayInDelhi();
    return days.has(today) ? today : [...days.keys()].sort()[0];
  }

  function renderDay(key) {
    const day = days.get(key);
    if (!day) return;
    const selected = $("#selected-date-title");
    selected.textContent = dateLabels.format(dateFor(key));
    $("#selected-date-masa").textContent = `${day.masa} Masa · Gaurabda ${day.gaurabda}`;
    const facts = [
      ["Tithi", day.tithi],
      ["Paksa", `${day.paksa} (${day.paksaCode})`],
      ["Nakshatra", day.nakshatra]
    ];
    $("#selected-date-facts").innerHTML = facts.map(([label, value]) => `<div class="calendar-fact"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join("");

    const entries = [];
    if (day.fastName) entries.push(`<li><strong>Fast:</strong> ${esc(day.fastName)}</li>`);
    if (day.parana) entries.push(`<li><strong>Parana:</strong> ${esc(day.parana)} IST · Delhi local time</li>`);
    for (const item of day.events) {
      if (item.kind === "fasting") continue;
      entries.push(`<li class="${esc(item.kind)}">${esc(item.name)}</li>`);
    }
    $("#selected-date-observances").innerHTML = entries.length
      ? `<ul class="calendar-observance-list">${entries.join("")}</ul>`
      : `<p class="calendar-empty-note">No festival or acharya observance is listed for this date in the Delhi source file.</p>`;
    document.querySelectorAll(".calendar-day[data-date]").forEach(button => {
      const active = button.dataset.date === key;
      button.classList.toggle("is-selected", active);
      button.setAttribute("aria-pressed", String(active));
    });
    renderGaurabda(key);
  }

  function renderGaurabda(selectedKey) {
    const selected = days.get(selectedKey);
    if (selected) $("#current-gaurabda-month").textContent = `${selected.masa} Masa · Gaurabda ${selected.gaurabda}`;

    const visible = [...days.values()].filter(day => day.year === viewYear && day.month === viewMonth);
    const masas = [...new Set(visible.map(day => `${day.masa} Masa`))];
    const note = masas.length > 1
      ? `This Gregorian month crosses ${masas.join(" and ")}. The selected date is shown above.`
      : masas.length === 1
        ? `${masas[0]} falls within ${monthNames[viewMonth]} ${viewYear}.`
        : "This month is outside the available Delhi source files.";
    $("#month-transition-note").textContent = note;
  }

  let viewYear = 2026;
  let viewMonth = 0;
  let selectedKey = "";

  function renderMonth() {
    const first = new Date(Date.UTC(viewYear, viewMonth, 1));
    const length = new Date(Date.UTC(viewYear, viewMonth + 1, 0)).getUTCDate();
    const start = first.getUTCDay();
    $("#month-title").textContent = monthLabels.format(first);
    const cells = [];
    for (let i = 0; i < start; i++) cells.push(`<span class="calendar-day calendar-day--empty" aria-hidden="true"></span>`);

    for (let number = 1; number <= length; number++) {
      const key = keyFor(viewYear, viewMonth, number);
      const day = days.get(key);
      if (!day) {
        cells.push(`<span class="calendar-day calendar-day--empty" aria-hidden="true"></span>`);
        continue;
      }
      const types = new Set(day.events.map(item => item.kind === "fasting-note" ? "fasting" : item.kind));
      if (day.fastName) types.add("fasting");
      if (day.parana) types.add("parana");
      const typeNames = ["fasting", "parana", "festival", "acharya"].filter(type => types.has(type));
      const badge = day.fastName || day.events.find(item => item.kind !== "fasting")?.name || (day.parana ? "Parana" : "");
      const aria = `${dateLabels.format(dateFor(key))}, ${day.tithi}, ${day.masa} Masa, Gaurabda ${day.gaurabda}${day.fastName ? `, fasting for ${day.fastName}` : ""}${day.parana ? `, Parana ${day.parana}` : ""}`;
      cells.push(`<button class="calendar-day${selectedKey === key ? " is-selected" : ""}" type="button" role="gridcell" data-date="${key}" aria-label="${esc(aria)}" aria-pressed="${selectedKey === key}"><span class="calendar-day__number">${number}</span>${badge ? `<span class="calendar-day__label ${typeNames[0] || "festival"}">${esc(badge)}</span>` : ""}${typeNames.length ? `<span class="calendar-day__dots" aria-hidden="true">${typeNames.map(type => `<i class="${type}"></i>`).join("")}</span>` : ""}</button>`);
    }
    $("#calendar-days").innerHTML = cells.join("");
    $("#calendar-days").querySelectorAll("button[data-date]").forEach(button => button.addEventListener("click", () => {
      selectedKey = button.dataset.date;
      renderMonth();
      renderDay(selectedKey);
    }));
    $("#previous-month").disabled = viewYear === 2026 && viewMonth === 0;
    $("#next-month").disabled = viewYear === 2027 && viewMonth === 11;
    renderGaurabda(selectedKey);
  }

  function upcomingItems() {
    const today = todayInDelhi();
    const items = [];
    for (const day of [...days.values()].filter(item => item.key >= today).sort((a, b) => a.key.localeCompare(b.key))) {
      if (day.fastName) {
        const following = days.get(keyFor(day.year, day.month, day.day + 1));
        items.push({ key: day.key, kind: "fasting", name: day.fastName, paranaDate: following?.parana ? following.key : "", parana: following?.parana || "" });
      }
      for (const event of day.events) {
        if (event.kind !== "fasting") items.push({ key: day.key, kind: event.kind, name: event.name });
      }
    }
    return items.sort((a, b) => a.key.localeCompare(b.key));
  }

  function renderUpcoming(filter = "all") {
    const filtered = upcomingItems().filter(item => filter === "all" || item.kind === filter);
    const shown = filtered.slice(0, filter === "fasting" ? 60 : 21);
    $("#upcoming-status").textContent = shown.length
      ? `Showing ${shown.length}${filtered.length > shown.length ? ` of ${filtered.length}` : ""} upcoming observances from the Delhi source files.`
      : "No matching future observances remain in the included Delhi files.";
    $("#upcoming-observances").innerHTML = shown.map(item => {
      const date = dateLabels.format(dateFor(item.key));
      const tag = item.kind === "fasting" ? "Ekadashi fast" : item.kind === "fasting-note" ? "Fasting note" : item.kind === "acharya" ? "Acharya day" : "Festival";
      const tagClass = item.kind === "fasting-note" ? "fasting" : item.kind;
      const parana = item.kind === "fasting"
        ? item.parana
          ? `<p><strong>Parana:</strong> ${esc(dateLabels.format(dateFor(item.paranaDate)))} · ${esc(item.parana)} IST</p>`
          : `<p>Parana timing is not listed in the included Delhi source.</p>`
        : "";
      return `<article class="upcoming-card"><span class="upcoming-card__date">${esc(date)}</span><span class="upcoming-card__tag ${tagClass}">${tag}</span><h3>${esc(item.name)}</h3>${parana}</article>`;
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

  async function loadSource(year) {
    const response = await fetch(`calendar-data/delhi-${year}.txt`, { cache: "no-cache" });
    if (!response.ok) throw new Error(`Could not load the ${year} Delhi calendar file.`);
    parseSource(await response.text());
  }

  async function start() {
    const status = $("#calendar-status");
    try {
      await Promise.all([loadSource(2026), loadSource(2027)]);
      selectedKey = currentDayKey();
      const selected = days.get(selectedKey);
      viewYear = selected.year;
      viewMonth = selected.month;
      renderMonth();
      renderDay(selectedKey);
      renderUpcoming();
      status.textContent = "Delhi source files loaded · local times shown in IST.";
      status.classList.add("is-ready");
    } catch (error) {
      status.textContent = "The interactive calendar could not load. Use the Delhi TXT and ICS downloads below.";
      status.classList.add("is-error");
      console.error(error);
    }

    $("#previous-month").addEventListener("click", () => {
      if (viewYear === 2026 && viewMonth === 0) return;
      moveMonth(-1);
    });
    $("#next-month").addEventListener("click", () => {
      if (viewYear === 2027 && viewMonth === 11) return;
      moveMonth(1);
    });
    document.querySelectorAll(".calendar-filter").forEach(button => button.addEventListener("click", () => {
      document.querySelectorAll(".calendar-filter").forEach(item => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      renderUpcoming(button.dataset.filter);
    }));

    const feed = new URL("calendar-data/delhi-vaisnava-2026-2027.ics", window.location.href);
    $("#calendar-feed-url").value = feed.href;
    $("#copy-feed-url").addEventListener("click", async () => {
      const status = $("#copy-status");
      try {
        await navigator.clipboard.writeText(feed.href);
        status.textContent = "Feed URL copied.";
      } catch {
        $("#calendar-feed-url").select();
        status.textContent = "Select and copy the feed URL.";
      }
    });
  }

  start();
})();
