(() => {
  const API = (window.FARMLINK_API_URL || "https://farmlinkdistribution.onrender.com").replace(/\/$/, "") + "/api";

  const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));

  function ga(eventName, params = {}) {
    if (typeof window.gtag === "function") {
      window.gtag("event", eventName, params);
    }
  }

  function pageFilters() {
    const path = location.pathname.split("/").filter(Boolean);
    if (path[0] === "cities" && path[1]) {
      return { location: document.body.dataset.seoName || path[1].replace(/-/g, " "), product: "" };
    }
    if (path[0] === "provinces" && path[1]) {
      return { location: document.body.dataset.seoName || path[1].replace(/-/g, " "), product: "" };
    }
    if (path[0] === "products" && path[1]) {
      return { location: "", product: document.body.dataset.seoName || path[1].replace(/-/g, " ") };
    }
    return { location: "", product: "" };
  }

  async function getJson(path) {
    const response = await fetch(`${API}${path}`, { headers: { "Accept": "application/json" } });
    if (!response.ok) throw new Error(`Request failed (${response.status})`);
    return response.json();
  }

  function supplierCard(item) {
    const availability = Number(item.available_trays || 0);
    return `
      <article class="live-supplier-card">
        <div class="live-supplier-top">
          <span class="live-supplier-mark">${esc((item.farm_name || "F").slice(0, 2).toUpperCase())}</span>
          <div>
            <h3>${esc(item.farm_name)}</h3>
            <p>${esc(item.location)}</p>
          </div>
        </div>
        <dl>
          <div><dt>Producer type</dt><dd>${esc(item.producer_type)}</dd></div>
          <div><dt>Weekly capacity</dt><dd>${Number(item.weekly_capacity || 0).toLocaleString("en-ZA")}</dd></div>
          <div><dt>Packaging</dt><dd>${esc(item.packaging || "Confirm with FarmLink")}</dd></div>
          <div><dt>Live availability</dt><dd>${availability > 0 ? `${availability.toLocaleString("en-ZA")} trays` : "Confirm availability"}</dd></div>
        </dl>
        <a class="live-supplier-cta" href="/#portal" data-marketplace-enquiry="${esc(item.reference)}">
          Request supplier matching
        </a>
      </article>`;
  }

  async function loadLiveMarketplace() {
    const target = document.querySelector("[data-live-marketplace]");
    if (!target) return;

    const { location: locationFilter, product } = pageFilters();
    const params = new URLSearchParams({ limit: "6" });
    if (locationFilter) params.set("location", locationFilter);
    if (product) params.set("product", product);

    target.innerHTML = `<div class="live-marketplace-loading">Checking approved supplier recordsâ€¦</div>`;

    try {
      const data = await getJson(`/marketplace/suppliers?${params.toString()}`);
      if (!data.items?.length) {
        target.innerHTML = `
          <div class="live-marketplace-empty">
            <strong>No public supplier listings match this page yet.</strong>
            <p>FarmLink may still coordinate the requirement through its reviewed supplier network.</p>
            <a href="/#portal" class="live-supplier-cta" data-marketplace-enquiry="empty-state">
              Submit a commercial requirement
            </a>
          </div>`;
      } else {
        target.innerHTML = `<div class="live-supplier-grid">${data.items.map(supplierCard).join("")}</div>`;
      }
      ga("marketplace_list_view", {
        page_location_filter: locationFilter || "national",
        page_product_filter: product || "all",
        result_count: Number(data.count || 0)
      });
    } catch (error) {
      console.error("Live marketplace loading error:", error);
      target.innerHTML = `
        <div class="live-marketplace-empty">
          <strong>Supplier listings are temporarily unavailable.</strong>
          <p>You can still submit your requirement directly to FarmLink.</p>
          <a href="/#portal" class="live-supplier-cta" data-marketplace-enquiry="fallback">
            Submit a commercial requirement
          </a>
        </div>`;
    }
  }

  document.addEventListener("click", event => {
    const enquiry = event.target.closest("[data-marketplace-enquiry]");
    if (enquiry) {
      ga("generate_lead", {
        lead_source: "seo_marketplace_page",
        supplier_reference: enquiry.dataset.marketplaceEnquiry || "general",
        page_path: location.pathname
      });
    }

    const phone = event.target.closest('a[href^="tel:"]');
    if (phone) ga("click_to_call", { page_path: location.pathname });

    const portal = event.target.closest('a[href*="#portal"]');
    if (portal) ga("portal_cta_click", { page_path: location.pathname });
  });

  document.addEventListener("DOMContentLoaded", loadLiveMarketplace);
})();
