/* FarmLink Mobile Navigation Stability Fix V2 */
(() => {
  "use strict";

  function resetMobileNavigation() {
    const drawer = document.querySelector(".fl-nav-drawer");
    const backdrop = document.querySelector(".fl-mobile-backdrop");
    const toggle = document.querySelector(".fl-nav-toggle");

    document.body.classList.remove("fl-nav-open");

    if (drawer) {
      drawer.classList.remove("is-open");
      drawer.setAttribute("aria-hidden", "true");
    }

    if (backdrop) {
      backdrop.classList.remove("is-open");
    }

    if (toggle) {
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "Open navigation");
    }
  }

  function bindSafetyHandlers() {
    const drawer = document.querySelector(".fl-nav-drawer");
    const backdrop = document.querySelector(".fl-mobile-backdrop");
    const toggle = document.querySelector(".fl-nav-toggle");

    if (!drawer || !backdrop || !toggle) return;

    const setOpen = open => {
      document.body.classList.toggle("fl-nav-open", open);
      drawer.classList.toggle("is-open", open);
      backdrop.classList.toggle("is-open", open);
      drawer.setAttribute("aria-hidden", String(!open));
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute(
        "aria-label",
        open ? "Close navigation" : "Open navigation"
      );
    };

    /* Replace old handlers with a clean clone. */
    const replacement = toggle.cloneNode(true);
    toggle.replaceWith(replacement);

    replacement.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      const open = replacement.getAttribute("aria-expanded") !== "true";
      setOpen(open);
    });

    backdrop.addEventListener("click", () => setOpen(false));

    drawer.addEventListener("click", event => {
      if (event.target.closest("a")) setOpen(false);
    });

    document.addEventListener("keydown", event => {
      if (event.key === "Escape") setOpen(false);
    });

    window.addEventListener("pageshow", () => setOpen(false));
    window.addEventListener("orientationchange", () => setOpen(false));
    window.addEventListener("resize", () => {
      if (window.innerWidth > 920) setOpen(false);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    resetMobileNavigation();
    requestAnimationFrame(bindSafetyHandlers);
  });
})();
