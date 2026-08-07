/* FarmLink Mobile Navigation V3 - Remove duplicates and normalize drawer */
(() => {
  "use strict";

  function isMenuLikeButton(element) {
    if (!element || element.tagName !== "BUTTON") return false;
    const text = (element.textContent || "").trim().toLowerCase();
    const aria = (element.getAttribute("aria-label") || "").toLowerCase();
    const cls = element.className || "";
    return (
      element.classList.contains("fl-nav-toggle") ||
      cls.includes("menu-toggle") ||
      cls.includes("hamburger") ||
      aria.includes("menu") ||
      aria.includes("navigation") ||
      text === "menu"
    );
  }

  function resetState() {
    document.body.classList.remove("fl-nav-open");
    document.querySelectorAll(".fl-nav-drawer").forEach(drawer => {
      drawer.classList.remove("is-open");
      drawer.setAttribute("aria-hidden", "true");
    });
    document.querySelectorAll(".fl-mobile-backdrop").forEach(backdrop => {
      backdrop.classList.remove("is-open");
    });
    document.querySelectorAll(".fl-nav-toggle").forEach(toggle => {
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  function normalizeNavigation() {
    const header = document.querySelector(".fl-site-header");
    const drawer = document.querySelector(".fl-nav-drawer");
    const backdrop = document.querySelector(".fl-mobile-backdrop");
    if (!header || !drawer || !backdrop) return;

    const allMenuButtons = [...document.querySelectorAll("button")].filter(isMenuLikeButton);

    let primaryToggle =
      [...header.querySelectorAll("button")].find(button =>
        button.classList.contains("fl-nav-toggle")
      ) ||
      allMenuButtons.find(button => header.contains(button));

    if (!primaryToggle) return;

    primaryToggle.classList.add("fl-nav-toggle");

    allMenuButtons.forEach(button => {
      if (button === primaryToggle) return;
      button.classList.add("fl-nav-toggle-duplicate");
      button.setAttribute("aria-hidden", "true");
      button.tabIndex = -1;
    });

    [...drawer.querySelectorAll("button")].forEach(button => {
      if (isMenuLikeButton(button)) {
        button.remove();
      }
    });

    let drawerHead = drawer.querySelector(".fl-nav-drawer-head");
    if (!drawerHead) {
      drawerHead = document.createElement("div");
      drawerHead.className = "fl-nav-drawer-head";
      drawerHead.innerHTML = `
        <strong>Navigation</strong>
        <button type="button" class="fl-nav-close" aria-label="Close navigation">&times;</button>
      `;
      drawer.insertBefore(drawerHead, drawer.firstChild);
    }

    const closeButton = drawerHead.querySelector(".fl-nav-close");

    const setOpen = open => {
      document.body.classList.toggle("fl-nav-open", open);
      drawer.classList.toggle("is-open", open);
      backdrop.classList.toggle("is-open", open);
      drawer.setAttribute("aria-hidden", String(!open));
      primaryToggle.setAttribute("aria-expanded", String(open));
      primaryToggle.setAttribute(
        "aria-label",
        open ? "Close navigation" : "Open navigation"
      );
    };

    const cleanToggle = primaryToggle.cloneNode(true);
    primaryToggle.replaceWith(cleanToggle);
    primaryToggle = cleanToggle;

    primaryToggle.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      setOpen(primaryToggle.getAttribute("aria-expanded") !== "true");
    });

    closeButton?.addEventListener("click", () => setOpen(false));
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
    resetState();
    requestAnimationFrame(() => requestAnimationFrame(normalizeNavigation));
  });
})();
