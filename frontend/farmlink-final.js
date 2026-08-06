/* FarmLink Final Experience Layer */
(() => {
  function normalizeNavigation() {
    document.querySelectorAll('a[href^="#"]').forEach(link => {
      link.addEventListener("click", event => {
        const target = document.querySelector(link.getAttribute("href"));
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({behavior:"smooth",block:"start"});
      });
    });
  }

  function addExperienceRail() {
    if (document.getElementById("farmlinkJourney")) return;
    const anchor = document.querySelector("main") || document.body;
    const section = document.createElement("section");
    section.id = "farmlinkJourney";
    section.className = "fl-journey";
    section.innerHTML = `
      <div class="container">
        <p class="eyebrow">One connected agricultural ecosystem</p>
        <h2>From an idea to a completed commercial transaction.</h2>
        <div class="fl-journey-grid">
          ${[
            ["01","Register","Farmers, buyers and agricultural entrepreneurs enter one secure system."],
            ["02","Build","AgriStart profiles, mentorship, documents and funding readiness prepare businesses."],
            ["03","Activate","Verified entrepreneurs become approved suppliers and publish marketplace listings."],
            ["04","Match","Explainable matching connects supplier capacity to real buyer demand."],
            ["05","Trade","Quotations, orders, invoices, payment, fulfilment and supplier payouts close the loop."]
          ].map(([n,t,d])=>`<article><span>${n}</span><h3>${t}</h3><p>${d}</p></article>`).join("")}
        </div>
      </div>`;
    const footer = document.querySelector("footer");
    if (footer) footer.insertAdjacentElement("beforebegin", section);
    else anchor.appendChild(section);
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.documentElement.classList.add("farmlink-final");
    normalizeNavigation();
    addExperienceRail();
  });
})();
