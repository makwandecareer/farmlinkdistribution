/* FarmLink AgriStart Phase 3 public workspace */
(() => {
  const documentTypes = [
    "ID Document","CIPC Registration","Tax Compliance","B-BEE Affidavit",
    "Bank Confirmation Letter","Business Plan","Cash-flow Projection",
    "Pitch Deck","Company Profile","Proof of Address","Supplier Quotation",
    "Funding Application","Financial Statements"
  ];

  const escP3 = value => String(value ?? "")
    .replaceAll("&","&amp;").replaceAll("<","&lt;")
    .replaceAll(">","&gt;").replaceAll('"',"&quot;");

  function template() {
    return `
      <section id="business-workspace" class="section p3-public">
        <div class="container">
          <div class="p3-public-head">
            <p class="eyebrow">AgriStart Phase 3</p>
            <h2>Your Business Workspace and Document Centre</h2>
            <p>Use your AgriStart reference and registered email to review progress, tasks, funding readiness, mentorship and document status.</p>
          </div>

          <form id="p3AccessForm" class="p3-access-card">
            <label>AgriStart reference<input name="reference" required placeholder="AGR-..."></label>
            <label>Registered email<input name="email" type="email" required></label>
            <button class="button primary" type="submit">Open workspace</button>
          </form>

          <div id="p3PublicWorkspace" class="p3-public-workspace" hidden></div>
        </div>
      </section>`;
  }

  function mount() {
    if (document.getElementById("business-workspace")) return;
    const anchor = document.getElementById("business-launch")
      || document.getElementById("funding-service-registration")
      || document.getElementById("agristart")
      || document.querySelector("footer");
    if (!anchor) return;
    if (anchor.tagName.toLowerCase() === "footer") {
      anchor.insertAdjacentHTML("beforebegin", template());
    } else {
      anchor.insertAdjacentHTML("afterend", template());
    }
  }

  function render(data, credentials) {
    const host = document.getElementById("p3PublicWorkspace");
    const readiness = data.readiness || {};
    const workspace = data.workspace || {};
    const applicant = data.applicant || {};
    const tasks = data.tasks || [];
    const documents = data.documents || [];

    host.hidden = false;
    host.innerHTML = `
      <div class="p3-public-summary">
        <article><span>Applicant</span><strong>${escP3(applicant.full_name)}</strong><small>${escP3(applicant.reference)}</small></article>
        <article><span>Overall readiness</span><strong>${readiness.overall || 0}%</strong><small>Business activation score</small></article>
        <article><span>Funding</span><strong>${escP3(workspace.funding_status)}</strong><small>${escP3(workspace.next_action || "No next action")}</small></article>
        <article><span>Launch</span><strong>${escP3(workspace.launch_status)}</strong><small>${escP3(workspace.marketplace_status)}</small></article>
      </div>

      <div class="p3-public-grid">
        <article class="p3-panel">
          <h3>Readiness breakdown</h3>
          ${["documents","business","mentorship","funding","launch"].map(key=>`
            <div class="p3-score-row"><span>${key[0].toUpperCase()+key.slice(1)}</span><div><i style="width:${readiness[key] || 0}%"></i></div><b>${readiness[key] || 0}</b></div>`).join("")}
        </article>

        <article class="p3-panel">
          <h3>Current tasks</h3>
          ${tasks.length ? tasks.map(task=>`
            <div class="p3-item"><strong>${escP3(task.title)}</strong><span>${escP3(task.status)}${task.due_date ? ` - Due ${escP3(task.due_date)}` : ""}</span></div>`).join("") : `<p>No tasks have been assigned.</p>`}
        </article>

        <article class="p3-panel full">
          <h3>Document status</h3>
          <div class="p3-doc-list">
            ${documents.length ? documents.map(doc=>`
              <div><strong>${escP3(doc.document_type)}</strong><span>${escP3(doc.filename)}</span><b>${escP3(doc.review_status)}</b></div>`).join("") : `<p>No documents uploaded yet.</p>`}
          </div>
        </article>

        <article class="p3-panel full">
          <h3>Upload a document</h3>
          <form id="p3DocumentForm" class="p3-upload-form">
            <select name="document_type" required><option value="">Select document type</option>${documentTypes.map(type=>`<option>${type}</option>`).join("")}</select>
            <input name="file" type="file" accept=".pdf,.jpg,.jpeg,.png,.docx,.xlsx" required>
            <button class="button secondary" type="submit">Upload document</button>
          </form>
          <p id="p3UploadResult"></p>
        </article>
      </div>`;

    document.getElementById("p3DocumentForm").onsubmit = async event => {
      event.preventDefault();
      const result = document.getElementById("p3UploadResult");
      const formData = new FormData(event.currentTarget);
      formData.append("reference", credentials.reference);
      formData.append("email", credentials.email);
      try {
        const response = await fetch("/api/public/phase3/documents", {
          method:"POST",
          body:formData
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "Upload failed");
        result.textContent = `Uploaded successfully. Document reference: ${payload.reference}`;
        event.currentTarget.reset();
      } catch (error) {
        result.textContent = error.message;
      }
    };
  }

  document.addEventListener("DOMContentLoaded", () => {
    mount();
    document.getElementById("p3AccessForm")?.addEventListener("submit", async event => {
      event.preventDefault();
      const form = event.currentTarget;
      const credentials = Object.fromEntries(new FormData(form).entries());
      const button = form.querySelector("button");
      button.disabled = true;
      button.textContent = "Opening...";
      try {
        const response = await fetch("/api/public/phase3/workspace", {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body:JSON.stringify(credentials)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Workspace could not be opened");
        render(data, credentials);
        document.getElementById("p3PublicWorkspace").scrollIntoView({behavior:"smooth"});
      } catch (error) {
        alert(error.message);
      } finally {
        button.disabled = false;
        button.textContent = "Open workspace";
      }
    });
  });
})();
