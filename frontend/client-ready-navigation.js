/* FarmLink Client-Ready Navigation V5 */
(() => {
  "use strict";

  const OLD_SELECTORS = [
    ".fl-nav-toggle",
    ".fl-nav-drawer",
    ".fl-mobile-backdrop",
    ".fl-nav-drawer-head",
    ".fl-nav-close",
    ".fl-nav-toggle-duplicate"
  ];

  function removeOldNavigationArtifacts() {
    OLD_SELECTORS.forEach(selector => {
      document.querySelectorAll(selector).forEach(node => node.remove());
    });
    document.body.classList.remove("fl-nav-open");
  }

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

  function findCta(header, nav) {
    return [...header.querySelectorAll("a, button")].find(element => {
      if (nav.contains(element)) return false;
      const text = (element.textContent || "").trim().toLowerCase();
      return text.includes("register") || text.includes("order");
    });
  }

  function cloneLinks(nav) {
    const mobileNav = document.createElement("nav");
    mobileNav.className = "fl-client-mobile-nav";
    mobileNav.setAttribute("aria-label", "Mobile navigation");

    [...nav.querySelectorAll("a")].forEach(link => {
      mobileNav.appendChild(link.cloneNode(true));
    });

    return mobileNav;
  }

  function buildClientNavigation() {
    removeOldNavigationArtifacts();

    const header = findHeader();
    if (!header || header.dataset.clientNavigation === "true") return;

    const nav = findNav(header);
    const brand = findBrand(header);
    if (!nav || !brand) return;

    header.dataset.clientNavigation = "true";
    header.classList.add("fl-client-header");

    let inner = header.querySelector(".container");
    if (!inner) {
      inner = document.createElement("div");
      while (header.firstChild) inner.appendChild(header.firstChild);
      header.appendChild(inner);
    }
    inner.classList.add("fl-client-header-inner");

    brand.classList.add("fl-client-brand");
    nav.classList.add("fl-client-desktop-nav");

    const cta = findCta(header, nav);
    if (cta) cta.classList.add("fl-client-cta");

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "fl-client-menu-toggle";
    toggle.setAttribute("aria-label", "Open navigation");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-controls", "flClientDrawer");
    toggle.innerHTML = "<span></span>";
    inner.appendChild(toggle);

    const backdrop = document.createElement("div");
    backdrop.className = "fl-client-backdrop";
    document.body.appendChild(backdrop);

    const drawer = document.createElement("aside");
    drawer.id = "flClientDrawer";
    drawer.className = "fl-client-drawer";
    drawer.setAttribute("aria-hidden", "true");

    const drawerHeader = document.createElement("div");
    drawerHeader.className = "fl-client-drawer-header";
    drawerHeader.innerHTML = `
      <strong>Menu</strong>
      <button type="button" class="fl-client-close" aria-label="Close navigation">&times;</button>
    `;
    drawer.appendChild(drawerHeader);
    drawer.appendChild(cloneLinks(nav));

    if (cta) {
      const mobileCtaWrap = document.createElement("div");
      mobileCtaWrap.className = "fl-client-mobile-cta";
      const mobileCta = cta.cloneNode(true);
      mobileCta.classList.add("fl-client-cta");
      mobileCtaWrap.appendChild(mobileCta);
      drawer.appendChild(mobileCtaWrap);
    }

    document.body.appendChild(drawer);

    const setOpen = open => {
      document.body.classList.toggle("fl-client-menu-open", open);
      drawer.classList.toggle("is-open", open);
      backdrop.classList.toggle("is-open", open);
      drawer.setAttribute("aria-hidden", String(!open));
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute(
        "aria-label",
        open ? "Close navigation" : "Open navigation"
      );
    };

    toggle.addEventListener("click", () => {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    drawer.querySelector(".fl-client-close").addEventListener("click", () => {
      setOpen(false);
    });

    backdrop.addEventListener("click", () => setOpen(false));

    drawer.addEventListener("click", event => {
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

    setOpen(false);
  }

  document.addEventListener("DOMContentLoaded", () => {
    requestAnimationFrame(buildClientNavigation);
  });
})();
