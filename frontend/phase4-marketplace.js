/* FarmLink Verified Supplier Marketplace - Permanent Fix V2 */
(() => {
  "use strict";

  const API_ORIGIN = (
    window.FARMLINK_API_URL ||
    document.documentElement.dataset.apiOrigin ||
    "https://farmlinkdistribution.onrender.com"
  ).replace(/\/+$/, "");

  const ENDPOINTS = [
    `${API_ORIGIN}/api/public/phase4/suppliers`,
    `${API_ORIGIN}/api/marketplace/suppliers`
  ];

  const esc = value => String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

  async function fetchJson(url) {
    const response = await fetch(url, {
      method: "GET",
      mode: "cors",
      cache: "no-store",
      headers: { Accept: "application/json" }
    });

    const text = await response.text();
    let payload = null;

    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (_) {
        payload = null;
      }
    }

    if (!response.ok) {
      const detail =
        payload?.detail ||
        payload?.message ||
        text.trim() ||
        `HTTP ${response.status}`;
      const error = new Error(detail);
      error.status = response.status;
      throw error;
    }

    if (payload === null) {
      throw new Error("The supplier API returned a non-JSON response.");
    }

    return payload;
  }

  function mapLegacySupplier(item) {
    return {
      reference: item.reference,
      business_name: item.farm_name,
      product_name: item.producer_type || item.egg_sizes || "Agricultural products",
      product_category: item.producer_type || "Agriculture",
      description:
        item.notes ||
        `${item.farm_name} supplies ${item.egg_sizes || "agricultural products"}.`,
      location: item.location,
      weekly_capacity: item.weekly_capacity || item.available_trays || 0,
      packaging: item.packaging,
      delivery_capability: item.delivery_capability,
      minimum_order: null,
      unit_price: null,
      featured: false
    };
  }

  async function loadSupplierData(params) {
    let lastError = null;

    for (const endpoint of ENDPOINTS) {
      try {
        const query = new URLSearchParams(params);

        if (endpoint.includes("/api/marketplace/suppliers")) {
          const product = query.get("q") || query.get("category") || "";
          const location = query.get("location") || "";
          query.delete("q");
          query.delete("category");
          if (product) query.set("product", product);
          if (location) query.set("location", location);
          query.set("limit", "24");
        }

        const payload = await fetchJson(`${endpoint}?${query.toString()}`);

        if (Array.isArray(payload)) {
          return payload;
        }

        if (Array.isArray(payload.items)) {
          return payload.items.map(mapLegacySupplier);
        }

        throw new Error("Supplier API returned an unsupported response format.");
      } catch (error) {
        lastError = error;
        if (error.status !== 404) break;
      }
    }

    throw lastError || new Error("Supplier marketplace could not be loaded.");
  }

  function template() {
    return `
      <section id="verified-supplier-marketplace" class="section p4-market">
        <div class="container">
          <div class="p4-head">
            <p class="eyebrow">Verified Supplier Marketplace</p>
            <h2>Discover supplier-ready agricultural businesses.</h2>
            <p>Search verified FarmLink suppliers by product, category and location. Buyer introductions are coordinated through FarmLink.</p>
          </div>

          <form id="p4SearchForm" class="p4-search">
            <input name="q" placeholder="Product or supplier">
            <input name="location" placeholder="Location">
            <input name="category" placeholder="Category">
            <button class="button primary" type="submit">Search suppliers</button>
          </form>

          <div id="p4SupplierResults" class="p4-results"></div>
        </div>
      </section>`;
  }

  function mount() {
    if (document.getElementById("verified-supplier-marketplace")) return;

    const anchor =
      document.getElementById("business-workspace") ||
      document.getElementById("marketplace") ||
      document.querySelector("footer");

    if (!anchor) return;

    if (anchor.tagName.toLowerCase() === "footer") {
      anchor.insertAdjacentHTML("beforebegin", template());
    } else {
      anchor.insertAdjacentHTML("afterend", template());
    }
  }

  function render(rows) {
    const host = document.getElementById("p4SupplierResults");
    if (!host) return;

    if (!rows.length) {
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
    const host = document.getElementById("p4SupplierResults");
    if (!host) return;

    host.innerHTML = `
      <div class="p4-empty p4-api-error">
        <strong>Supplier marketplace is temporarily unavailable.</strong>
        <span>${esc(error.message)}</span>
      </div>`;
  }

  async function load(params = new URLSearchParams()) {
    const host = document.getElementById("p4SupplierResults");
    if (!host) return;

    host.innerHTML = `<div class="p4-empty">Loading verified suppliers...</div>`;

    try {
      const rows = await loadSupplierData(params);
      render(rows);
    } catch (error) {
      console.error("FarmLink marketplace:", error);
      renderError(error);
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    mount();

    const form = document.getElementById("p4SearchForm");
    if (form) {
      form.addEventListener("submit", event => {
        event.preventDefault();
        load(new URLSearchParams(new FormData(form)));
      });
    }

    load();
  });
})();
