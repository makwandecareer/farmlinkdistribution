/* FarmLink Mobile Connected Tabs V6 */
(() => {
  "use strict";

  function findHeader() {
    return (
      document.querySelector("header") ||
      document.querySelector(".site-header") ||
      document.querySelector(".topbar")
    );
  }

  function findNav(header) {
    return header.querySelector("nav") || header.querySelector(".main-nav");
  }

  function findCta(header, nav) {
    return [...header.querySelectorAll("a, button")].find(element => {
      if (nav.contains(element)) return false;
      const text = (element.textContent || "").trim().toLowerCase();
      return text.includes("register") || text.includes("order");
    });
  }

  function buildMobileTabs() {
    const header = findHeader();
    if (!header || header.dataset.mobileTabsV6 === "true") return;

    const nav = findNav(header);
    if (!nav) return;

    header.dataset.mobileTabsV6 = "true";

    let headerInner = header.querySelector(".container") || header;
    const cta = findCta(header, nav);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "fl-mobile-tabs-toggle";
    toggle.setAttribute("aria-label", "Open menu");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", "flMobileTabsPanel");
    toggle.innerHTML = "<span></span>";
    headerInner.appendChild(toggle);

    const panel = document.createElement("div");
    panel.id = "flMobileTabsPanel";
    panel.className = "fl-mobile-tabs-panel";
    panel.setAttribute("aria-hidden", "true");

    const inner = document.createElement("div");
    inner.className = "fl-mobile-tabs-inner";

    const mobileNav = document.createElement("nav");
    mobileNav.className = "fl-mobile-tabs-nav";
    mobileNav.setAttribute("aria-label", "Mobile navigation");

    [...nav.querySelectorAll("a")].forEach(link => {
      const clone = link.cloneNode(true);
      mobileNav.appendChild(clone);
    });

    inner.appendChild(mobileNav);

    if (cta) {
      const ctaWrap = document.createElement("div");
      ctaWrap.className = "fl-mobile-tabs-cta";
      ctaWrap.appendChild(cta.cloneNode(true));
      inner.appendChild(ctaWrap);
    }

    panel.appendChild(inner);
    document.body.appendChild(panel);

    const backdrop = document.createElement("div");
    backdrop.className = "fl-mobile-tabs-backdrop";
    document.body.appendChild(backdrop);

    const setOpen = open => {
      document.body.classList.toggle("fl-mobile-tabs-open", open);
      panel.classList.toggle("is-open", open);
      backdrop.classList.toggle("is-open", open);
      panel.setAttribute("aria-hidden", String(!open));
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    };

    toggle.addEventListener("click", () => {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    backdrop.addEventListener("click", () => setOpen(false));

    panel.addEventListener("click", event => {
      if (event.target.closest("a")) setOpen(false);
    });

    document.addEventListener("keydown", event => {
      if (event.key === "Escape") setOpen(false);
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 920) setOpen(false);
    });

    window.addEventListener("orientationchange", () => setOpen(false));
    window.addEventListener("pageshow", () => setOpen(false));

    document.body.classList.add("fl-mobile-tabs-ready");
    setOpen(false);
  }

  document.addEventListener("DOMContentLoaded", buildMobileTabs);
})();
