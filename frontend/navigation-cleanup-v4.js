/* FarmLink Navigation Cleanup V4 */
(() => {
  "use strict";

  function cleanupDesktopNavigation() {
    const drawer = document.querySelector(".fl-nav-drawer");
    const drawerHead = drawer?.querySelector(".fl-nav-drawer-head");
    const toggle = document.querySelector(".fl-nav-toggle");
    const backdrop = document.querySelector(".fl-mobile-backdrop");

    if (window.innerWidth > 920) {
      document.body.classList.remove("fl-nav-open");
      drawer?.classList.remove("is-open");
      backdrop?.classList.remove("is-open");
      toggle?.setAttribute("aria-expanded", "false");

      if (drawerHead) {
        drawerHead.setAttribute("aria-hidden", "true");
      }
    } else if (drawerHead) {
      drawerHead.setAttribute("aria-hidden", "false");
    }
  }

  document.addEventListener("DOMContentLoaded", cleanupDesktopNavigation);
  window.addEventListener("resize", cleanupDesktopNavigation);
  window.addEventListener("orientationchange", cleanupDesktopNavigation);
})();
