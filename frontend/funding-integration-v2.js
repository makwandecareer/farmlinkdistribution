/* FarmLink funding-service registration V2 */
(() => {
  const services = {
    readiness_assessment: ["Funding Readiness Assessment", 499],
    application_support: ["Funding Application Support", 999],
    full_funding_pack: ["Full Funding Pack", 1999]
  };

  const provinces = [
    "Eastern Cape","Free State","Gauteng","KwaZulu-Natal","Limpopo",
    "Mpumalanga","North West","Northern Cape","Western Cape"
  ];

  function formHtml() {
    return `
      <section id="funding-service-registration" class="section fl-funding-register">
        <div class="container">
          <div class="fl-funding-title">
            <p class="eyebrow">Funding service registration</p>
            <h2>Register for paid professional funding assistance.</h2>
            <p>Select the service you need. The same service, fee and reference will appear in the FarmLink admin portal.</p>
          </div>

          <form id="flFundingForm" class="fl-funding-form">
            <div class="fl-funding-services">
              ${Object.entries(services).map(([code,[name,fee]])=>`
                <label>
                  <input type="radio" name="service_code" value="${code}" required>
                  <span><b>${name}</b><strong>R${fee.toLocaleString("en-ZA")}</strong><small>Once-off professional service</small></span>
                </label>`).join("")}
            </div>

            <div class="fl-funding-fields">
              <label>Full name *<input name="applicant_name" required></label>
              <label>Business or farm name<input name="business_name"></label>
              <label>Email address *<input name="email" type="email" required></label>
              <label>Phone number *<input name="phone" required></label>
              <label>Province *<select name="province" required><option value="">Select</option>${provinces.map(p=>`<option>${p}</option>`).join("")}</select></label>
              <label>Municipality or town<input name="municipality"></label>
              <label>Agricultural interest<input name="agricultural_interest"></label>
              <label>Existing AgriStart reference<input name="agristart_reference" placeholder="AGR-..."></label>
              <label>Funding amount required (R)<input name="funding_amount_required" type="number" min="0" step="0.01"></label>
              <label>Funding purpose<input name="funding_purpose"></label>
              <label class="full">Business idea or business description<textarea name="business_idea" rows="5"></textarea></label>
            </div>

            <div class="fl-funding-consent">
              <label><input name="consent_confirmed" type="checkbox" required> I consent to FarmLink processing this information for funding-readiness support.</label>
              <label><input name="terms_accepted" type="checkbox" required> I understand that the service is paid and payment does not guarantee funding approval.</label>
            </div>

            <button class="button primary" type="submit">Submit funding registration</button>
            <div id="flFundingResult" class="fl-funding-result" aria-live="polite"></div>
          </form>
        </div>
      </section>`;
  }

  function mount() {
    if (document.getElementById("funding-service-registration")) return;
    const anchor = document.getElementById("funding-services")
      || document.getElementById("funding-readiness")
      || document.getElementById("agristart")
      || document.querySelector("footer");
    if (!anchor) return;
    if (anchor.tagName.toLowerCase() === "footer") anchor.insertAdjacentHTML("beforebegin", formHtml());
    else anchor.insertAdjacentHTML("afterend", formHtml());
  }

  async function submit(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const resultBox = document.getElementById("flFundingResult");
    const button = form.querySelector('button[type="submit"]');
    const payload = Object.fromEntries(new FormData(form).entries());
    payload.consent_confirmed = form.elements.consent_confirmed.checked;
    payload.terms_accepted = form.elements.terms_accepted.checked;
    payload.funding_amount_required = payload.funding_amount_required
      ? Number(payload.funding_amount_required)
      : null;

    button.disabled = true;
    button.textContent = "Submitting...";
    resultBox.className = "fl-funding-result";
    resultBox.textContent = "";

    try {
      const response = await fetch("/api/public/funding-services", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map(item=>item.msg).join(", ")
          : data.detail;
        throw new Error(detail || "Registration failed");
      }

      resultBox.classList.add("success");
      resultBox.innerHTML = `<strong>Funding registration received.</strong><br>Reference: ${data.reference}<br>Service: ${data.service_name}<br>Fee: R${Number(data.service_fee).toLocaleString("en-ZA")}<br>Payment instructions will be issued before work begins.`;
      form.reset();
    } catch (error) {
      resultBox.classList.add("error");
      resultBox.textContent = error.message;
    } finally {
      button.disabled = false;
      button.textContent = "Submit funding registration";
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    mount();
    document.getElementById("flFundingForm")?.addEventListener("submit", submit);
    document.querySelectorAll(".funding-service-select").forEach(button => {
      button.addEventListener("click", () => {
        const mapping = {
          "Funding Readiness Assessment": "readiness_assessment",
          "Funding Application Support": "application_support",
          "Full Funding Pack": "full_funding_pack"
        };
        const code = mapping[button.dataset.fundingService];
        const form = document.getElementById("flFundingForm");
        const radio = form?.querySelector(`[name="service_code"][value="${code}"]`);
        if (radio) radio.checked = true;
        form?.scrollIntoView({behavior:"smooth",block:"start"});
      });
    });
  });
})();
