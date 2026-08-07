/* FarmLink Responsive Navigation V1 */
(() => {
  "use strict";

  function findHeader() {
    return (
      document.querySelector("header") ||
      document.querySelector(".site-header") ||
      document.querySelector(".topbar")
    );
  }

  function findBrand(header) {
    return (
      header.querySelector(".logo") ||
      header.querySelector(".brand") ||
      header.querySelector('a[href="/"]') ||
      header.querySelector("a")
    );
  }

  function findNav(header) {
    return header.querySelector("nav") || header.querySelector(".main-nav");
  }

  function findAction(header, nav) {
    const candidates = [...header.querySelectorAll("a, button")];
    return candidates.find(element => {
      if (nav?.contains(element)) return false;
      const text = (element.textContent || "").trim().toLowerCase();
      return text.includes("register") || text.includes("order");
    });
  }

  function closeNavigation(toggle, drawer, backdrop) {
    toggle.setAttribute("aria-expanded", "false");
    drawer.classList.remove("is-open");
    backdrop.classList.remove("is-open");
    document.body.classList.remove("fl-nav-open");
  }

  function buildNavigation() {
    const header = findHeader();
    if (!header || header.dataset.responsiveNavigation === "true") return;

    const nav = findNav(header);
    const brand = findBrand(header);
    if (!nav || !brand) return;

    header.dataset.responsiveNavigation = "true";
    header.classList.add("fl-site-header");

    let inner = header.querySelector(".container");
    if (!inner) {
      inner = document.createElement("div");
      while (header.firstChild) inner.appendChild(header.firstChild);
      header.appendChild(inner);
    }
    inner.classList.add("fl-site-header-inner");

    brand.classList.add("fl-site-brand");
    nav.classList.add("fl-site-nav");

    const action = findAction(header, nav);
    const drawer = document.createElement("div");
    drawer.className = "fl-nav-drawer";
    drawer.id = "flNavigationDrawer";

    nav.parentNode.insertBefore(drawer, nav);
    drawer.appendChild(nav);

    const actions = document.createElement("div");
    actions.className = "fl-site-actions";
    if (action) {
      actions.appendChild(action);
    }
    drawer.appendChild(actions);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "fl-nav-toggle";
    toggle.setAttribute("aria-label", "Open navigation");
    toggle.setAttribute("aria-controls", drawer.id);
    toggle.setAttribute("aria-expanded", "false");
    toggle.innerHTML = "<span></span>";
    inner.appendChild(toggle);

    const backdrop = document.createElement("div");
    backdrop.className = "fl-mobile-backdrop";
    document.body.appendChild(backdrop);

    toggle.addEventListener("click", () => {
      const open = toggle.getAttribute("aria-expanded") !== "true";
      toggle.setAttribute("aria-expanded", String(open));
      drawer.classList.toggle("is-open", open);
      backdrop.classList.toggle("is-open", open);
      document.body.classList.toggle("fl-nav-open", open);
    });

    backdrop.addEventListener("click", () => {
      closeNavigation(toggle, drawer, backdrop);
    });

    drawer.addEventListener("click", event => {
      if (event.target.closest("a")) {
        closeNavigation(toggle, drawer, backdrop);
      }
    });

    document.addEventListener("keydown", event => {
      if (event.key === "Escape") {
        closeNavigation(toggle, drawer, backdrop);
      }
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 920) {
        closeNavigation(toggle, drawer, backdrop);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", buildNavigation);
})();
