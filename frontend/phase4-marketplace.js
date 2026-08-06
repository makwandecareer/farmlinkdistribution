/* FarmLink AgriStart Phase 4 marketplace */
(() => {
  const esc4 = value => String(value ?? "")
    .replaceAll("&","&amp;").replaceAll("<","&lt;")
    .replaceAll(">","&gt;").replaceAll('"',"&quot;");

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
    const anchor = document.getElementById("business-workspace")
      || document.getElementById("marketplace")
      || document.querySelector("footer");
    if (!anchor) return;
    if (anchor.tagName.toLowerCase() === "footer") {
      anchor.insertAdjacentHTML("beforebegin", template());
    } else {
      anchor.insertAdjacentHTML("afterend", template());
    }
  }

  async function load(params = new URLSearchParams()) {
    const host = document.getElementById("p4SupplierResults");
    host.innerHTML = `<p>Loading verified suppliers...</p>`;
    try {
      const response = await fetch(`/api/public/phase4/suppliers?${params}`);
      const rows = await response.json();
      if (!response.ok) throw new Error(rows.detail || "Could not load suppliers");
      host.innerHTML = rows.length ? rows.map(item => `
        <article class="p4-card">
          ${item.featured ? `<span class="p4-featured">Featured</span>` : ""}
          <p class="eyebrow">${esc4(item.product_category)}</p>
          <h3>${esc4(item.product_name)}</h3>
          <strong>${esc4(item.business_name)}</strong>
          <p>${esc4(item.description)}</p>
          <dl>
            <div><dt>Location</dt><dd>${esc4(item.location)}</dd></div>
            <div><dt>Weekly capacity</dt><dd>${Number(item.weekly_capacity || 0).toLocaleString("en-ZA")}</dd></div>
            <div><dt>Packaging</dt><dd>${esc4(item.packaging || "Discuss with supplier")}</dd></div>
            <div><dt>Delivery</dt><dd>${esc4(item.delivery_capability)}</dd></div>
            <div><dt>Minimum order</dt><dd>${esc4(item.minimum_order || "On request")}</dd></div>
          </dl>
          <a class="button secondary full" href="#buyer-registration">Request a FarmLink introduction</a>
        </article>`).join("") : `<div class="p4-empty">No published suppliers match this search yet.</div>`;
    } catch (error) {
      host.innerHTML = `<div class="p4-empty">${esc4(error.message)}</div>`;
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    mount();
    load();
    document.getElementById("p4SearchForm")?.addEventListener("submit", event => {
      event.preventDefault();
      load(new URLSearchParams(new FormData(event.currentTarget)));
    });
  });
})();
