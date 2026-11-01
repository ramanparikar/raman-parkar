(() => {
  "use strict";
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector("#site-navigation");
  if (!toggle || !nav) return;

  document.documentElement.classList.add("has-site-menu");
  toggle.hidden = false;

  const closeMenu = (returnFocus = false) => {
    nav.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Open navigation");
    toggle.querySelector(".menu-label").textContent = "Menu";
    if (returnFocus) toggle.focus();
  };

  toggle.addEventListener("click", () => {
    const open = toggle.getAttribute("aria-expanded") !== "true";
    if (open) {
      nav.classList.add("is-open");
      toggle.setAttribute("aria-expanded", "true");
      toggle.setAttribute("aria-label", "Close navigation");
      toggle.querySelector(".menu-label").textContent = "Close";
    } else closeMenu();
  });

  nav.addEventListener("click", event => {
    if (event.target instanceof Element && event.target.closest("a")) closeMenu();
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && nav.classList.contains("is-open")) closeMenu(true);
  });

  document.addEventListener("pointerdown", event => {
    if (nav.classList.contains("is-open") && event.target instanceof Node &&
        !nav.contains(event.target) && !toggle.contains(event.target)) closeMenu();
  });

  window.addEventListener("resize", () => {
    if (window.matchMedia("(min-width: 961px)").matches) closeMenu();
  }, { passive: true });
})();
(() => {
  "use strict";
  const section = document.querySelector(".guides-section");
  if (!section || !("IntersectionObserver" in window)) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reducedMotion.matches) return;

  section.classList.add("guides-motion-ready");
  const observer = new IntersectionObserver((entries, activeObserver) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      section.classList.add("guides-is-visible");
      activeObserver.unobserve(entry.target);
      activeObserver.disconnect();
      break;
    }
  }, { rootMargin: "0px 0px -64px 0px", threshold: 0.12 });
  observer.observe(section);

  const showWithoutMotion = event => {
    if (!event.matches) return;
    observer.disconnect();
    section.classList.remove("guides-motion-ready", "guides-is-visible");
  };
  if (typeof reducedMotion.addEventListener === "function") {
    reducedMotion.addEventListener("change", showWithoutMotion);
  } else if (typeof reducedMotion.addListener === "function") {
    reducedMotion.addListener(showWithoutMotion);
  }
})();
