/* FarmLink Responsive Admin Navigation V1 */
(() => {
  "use strict";

  function findSidebar() {
    return (
      document.querySelector("aside") ||
      document.querySelector(".sidebar") ||
      document.getElementById("sidebar")
    );
  }

  function findHeader() {
    return (
      document.querySelector(".admin-header") ||
      document.querySelector(".topbar") ||
      document.querySelector("header")
    );
  }

  function closeMenu(sidebar, toggle, backdrop) {
    sidebar.classList.remove("fl-admin-sidebar-open");
    toggle.setAttribute("aria-expanded", "false");
    backdrop.classList.remove("is-open");
    document.body.classList.remove("fl-admin-menu-open");
  }

  function buildAdminNavigation() {
    const sidebar = findSidebar();
    const header = findHeader();
    if (!sidebar || !header || header.dataset.responsiveAdmin === "true") return;

    header.dataset.responsiveAdmin = "true";

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "fl-admin-mobile-toggle";
    toggle.setAttribute("aria-label", "Open administration menu");
    toggle.setAttribute("aria-expanded", "false");

    const headerContainer =
      header.querySelector(".container") ||
      header.querySelector(".toolbar") ||
      header;

    headerContainer.insertBefore(toggle, headerContainer.firstChild);

    const backdrop = document.createElement("div");
    backdrop.className = "fl-admin-backdrop";
    document.body.appendChild(backdrop);

    toggle.addEventListener("click", () => {
      const open = toggle.getAttribute("aria-expanded") !== "true";
      toggle.setAttribute("aria-expanded", String(open));
      sidebar.classList.toggle("fl-admin-sidebar-open", open);
      backdrop.classList.toggle("is-open", open);
      document.body.classList.toggle("fl-admin-menu-open", open);
    });

    backdrop.addEventListener("click", () => {
      closeMenu(sidebar, toggle, backdrop);
    });

    sidebar.addEventListener("click", event => {
      if (
        window.innerWidth <= 900 &&
        event.target.closest("button, a, [data-view]")
      ) {
        closeMenu(sidebar, toggle, backdrop);
      }
    });

    document.addEventListener("keydown", event => {
      if (event.key === "Escape") {
        closeMenu(sidebar, toggle, backdrop);
      }
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 900) {
        closeMenu(sidebar, toggle, backdrop);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", buildAdminNavigation);
})();
