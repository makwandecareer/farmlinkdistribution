/* FarmLink Homepage Marketplace API Fix V1 */
(() => {
  const DEFAULT_API_ORIGIN = "https://farmlinkdistribution-api.onrender.com";
  const API_ORIGIN = (
    window.FARMLINK_API_URL ||
    document.documentElement.dataset.apiOrigin ||
    DEFAULT_API_ORIGIN
  ).replace(/\/+$/, "");

  const esc = value => String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

  async function readJsonResponse(response) {
    const contentType = response.headers.get("content-type") || "";
    const raw = await response.text();

    if (!response.ok) {
      let detail = raw.trim() || `Request failed with status ${response.status}`;
      if (contentType.includes("application/json")) {
        try {
          const parsed = JSON.parse(raw);
          detail = parsed.detail || parsed.message || detail;
        } catch (_) {}
      }
      throw new Error(detail);
    }

    if (!contentType.includes("application/json")) {
      throw new Error(
        "The supplier API returned an invalid response. Check the API service URL."
      );
    }

    try {
      return JSON.parse(raw);
    } catch (_) {
      throw new Error("The supplier API returned malformed JSON.");
    }
  }

  async function supplierRequest(params = new URLSearchParams()) {
    const url = `${API_ORIGIN}/api/public/phase4/suppliers?${params.toString()}`;
    const response = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json"
      },
      mode: "cors",
      cache: "no-store"
    });
    return readJsonResponse(response);
  }

  function marketplaceHost() {
    return document.getElementById("p4SupplierResults");
  }

  function renderSuppliers(rows) {
    const host = marketplaceHost();
    if (!host) return;

    if (!Array.isArray(rows) || rows.length === 0) {
      host.innerHTML = `
        <div class="p4-empty">
          No verified suppliers match this search yet.
        </div>`;
      return;
    }

    host.innerHTML = rows.map(item => `
      <article class="p4-card">
        ${item.featured ? `<span class="p4-featured">Featured</span>` : ""}
        <p class="eyebrow">${esc(item.product_category)}</p>
        <h3>${esc(item.product_name)}</h3>
        <strong>${esc(item.business_name)}</strong>
        <p>${esc(item.description)}</p>
        <dl>
          <div><dt>Location</dt><dd>${esc(item.location)}</dd></div>
          <div><dt>Weekly capacity</dt><dd>${Number(item.weekly_capacity || 0).toLocaleString("en-ZA")}</dd></div>
          <div><dt>Packaging</dt><dd>${esc(item.packaging || "Discuss with supplier")}</dd></div>
          <div><dt>Delivery</dt><dd>${esc(item.delivery_capability || "On request")}</dd></div>
          <div><dt>Minimum order</dt><dd>${esc(item.minimum_order || "On request")}</dd></div>
        </dl>
        <a class="button secondary full" href="#portal" data-open-tab="buyer">
          Request a FarmLink introduction
        </a>
      </article>
    `).join("");
  }

  function renderError(error) {
    const host = marketplaceHost();
    if (!host) return;
    host.innerHTML = `
      <div class="p4-empty p4-api-error">
        <strong>Supplier marketplace is temporarily unavailable.</strong>
        <span>${esc(error.message)}</span>
      </div>`;
  }

  async function loadSuppliers(params = new URLSearchParams()) {
    const host = marketplaceHost();
    if (!host) return;

    host.innerHTML = `<div class="p4-empty">Loading verified suppliers...</div>`;

    try {
      const rows = await supplierRequest(params);
      renderSuppliers(rows);
    } catch (error) {
      console.error("FarmLink supplier marketplace error:", error);
      renderError(error);
    }
  }

  function bindSearch() {
    const form = document.getElementById("p4SearchForm");
    if (!form || form.dataset.apiFixBound === "true") return;

    form.dataset.apiFixBound = "true";
    form.addEventListener("submit", event => {
      event.preventDefault();
      loadSuppliers(new URLSearchParams(new FormData(form)));
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindSearch();
    loadSuppliers();
  });

  window.FarmLinkMarketplace = {
    apiOrigin: API_ORIGIN,
    reload: loadSuppliers
  };
})();
