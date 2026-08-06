/* FarmLink integrated funding administration V2 */
(() => {
  const VIEW = "fundingclients";
  const paymentStatuses = ["Not invoiced","Invoice issued","Awaiting payment","Part paid","Paid","Failed","Refunded","Cancelled"];
  const serviceStatuses = ["Application received","Assessment scheduled","Assessment in progress","Documents required","Ready to commence","Work in progress","Completed","Cancelled"];
  const fundingStatuses = ["Not started","Documents required","Funding ready","Application submitted","Under review","Approved","Declined"];
  const launchStatuses = ["Not started","In progress","At risk","Launch ready","Launched"];

  const escFl = value => String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
  const moneyFl = value => value == null ? "Not specified" : `R ${Number(value).toLocaleString("en-ZA",{minimumFractionDigits:2,maximumFractionDigits:2})}`;

  async function flApi(path, options={}) {
    if (typeof api === "function") return api(path, options);
    const token = localStorage.getItem("farmlink_token") || "";
    const response = await fetch(`/api${path}`, {
      ...options,
      headers: {"Content-Type":"application/json","Authorization":`Bearer ${token}`,...(options.headers||{})}
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Request failed");
    return data;
  }

  function ensureFundingView() {
    const nav = document.getElementById("nav");
    if (nav && !nav.querySelector(`[data-view="${VIEW}"]`)) {
      const button = document.createElement("button");
      button.dataset.view = VIEW;
      button.innerHTML = "<span>F</span>Funding service clients";
      const launch = nav.querySelector('[data-view="launchcentre"]');
      if (launch) launch.insertAdjacentElement("beforebegin", button);
      else nav.appendChild(button);
      button.onclick = () => window.showView(VIEW);
    }

    const host = document.querySelector("main") || document.getElementById("content") || document.getElementById("app");
    if (host && !document.getElementById(VIEW)) {
      const section = document.createElement("section");
      section.id = VIEW;
      section.className = "view";
      host.appendChild(section);
    }
  }

  async function loadFundingClients() {
    const view = document.getElementById(VIEW);
    view.innerHTML = `
      <div class="page-head">
        <div><span class="kicker">Paid funding services</span><h2>Funding Service Clients</h2><p class="muted">Homepage registrations, payments, readiness, funding applications and launch progress in one record.</p></div>
        <div class="toolbar fl-filters"><input id="flSearch" placeholder="Search clients"><select id="flPayFilter"><option value="all">All payments</option>${paymentStatuses.map(x=>`<option>${x}</option>`).join("")}</select><select id="flFundFilter"><option value="all">All funding statuses</option>${fundingStatuses.map(x=>`<option>${x}</option>`).join("")}</select></div>
      </div>
      <div id="flStats" class="fl-stats"></div>
      <div class="panel"><div id="flTable"></div></div>`;

    const render = async () => {
      const params = new URLSearchParams({
        q: document.getElementById("flSearch").value,
        payment_status: document.getElementById("flPayFilter").value,
        funding_status: document.getElementById("flFundFilter").value
      });
      const [stats,data] = await Promise.all([
        flApi("/admin/funding-services/dashboard"),
        flApi(`/admin/funding-services?${params}`)
      ]);

      document.getElementById("flStats").innerHTML = [
        ["Total registrations",stats.total,"All funding clients"],
        ["Awaiting payment",stats.awaiting_payment,"Work must not commence"],
        ["Paid clients",stats.paid,moneyFl(stats.paid_service_revenue)],
        ["Funding ready",stats.funding_ready,"Readiness completed"],
        ["Launched",stats.launched,"Commercially active"]
      ].map(([label,value,note])=>`<article><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`).join("");

      const rows = data.items || [];
      document.getElementById("flTable").innerHTML = rows.length ? `
        <div class="fl-table-wrap"><table class="table"><thead><tr><th>Client</th><th>Service</th><th>Fee</th><th>Payment</th><th>Readiness</th><th>Funding</th><th>Launch</th><th></th></tr></thead>
        <tbody>${rows.map(r=>`<tr>
          <td><strong>${escFl(r.applicant_name)}</strong><div class="ref">${escFl(r.reference)}</div><small>${escFl(r.agristart_reference || r.email)}</small></td>
          <td>${escFl(r.service_name)}<small>${escFl(r.service_status)}</small></td>
          <td>${moneyFl(r.service_fee)}</td>
          <td>${typeof badge==="function"?badge(r.payment_status):escFl(r.payment_status)}</td>
          <td><div class="fl-progress"><i style="width:${r.readiness_score}%"></i></div><small>${r.readiness_score}%</small></td>
          <td>${escFl(r.funding_status)}</td><td>${escFl(r.launch_status)}</td>
          <td><button onclick="openFundingClient(${r.id})">Manage</button></td>
        </tr>`).join("")}</tbody></table></div>` : `<div class="empty">No funding-service registrations yet.</div>`;
    };

    const db = typeof debounce==="function" ? debounce : (fn,ms)=>{let timer;return()=>{clearTimeout(timer);timer=setTimeout(fn,ms)}};
    document.getElementById("flSearch").oninput = db(render,250);
    document.getElementById("flPayFilter").onchange = render;
    document.getElementById("flFundFilter").onchange = render;
    await render();
  }

  window.openFundingClient = async id => {
    const [r,users] = await Promise.all([flApi(`/admin/funding-services/${id}`),flApi("/admin/users")]);
    const options = (items,current)=>items.map(x=>`<option ${x===current?"selected":""}>${x}</option>`).join("");
    const checked = key => r[key] ? "checked" : "";

    document.getElementById("drawerBody").innerHTML = `
      <span class="kicker">Integrated funding client</span><h2>${escFl(r.applicant_name)}</h2><p class="ref">${escFl(r.reference)}</p>
      <div class="fl-summary">
        <article><span>Service</span><strong>${escFl(r.service_name)}</strong><small>${moneyFl(r.service_fee)}</small></article>
        <article><span>Payment</span><strong>${escFl(r.payment_status)}</strong><small>${escFl(r.payment_reference||"No reference")}</small></article>
        <article><span>Readiness</span><strong>${r.readiness_score}%</strong><small>${escFl(r.funding_status)}</small></article>
        <article><span>Launch</span><strong>${escFl(r.launch_status)}</strong><small>${r.launch_readiness_score}% complete</small></article>
      </div>
      <form id="flClientForm">
        <h3>AgriStart and service</h3>
        <div class="form-grid">
          <label>AgriStart reference<input id="flAgriRef" value="${escFl(r.agristart_reference)}"></label>
          <label>AgriStart record ID<input id="flAgriId" type="number" value="${escFl(r.entrepreneur_application_id)}"></label>
          <label>Service status<select id="flServiceStatus">${options(serviceStatuses,r.service_status)}</select></label>
          <label>Assigned administrator<select id="flAssigned"><option value="">Unassigned</option>${users.filter(u=>u.is_active).map(u=>`<option value="${u.id}" ${u.id===r.assigned_to_id?"selected":""}>${escFl(u.full_name)}</option>`).join("")}</select></label>
        </div>

        <h3>Payment</h3>
        <div class="form-grid">
          <label>Payment status<select id="flPaymentStatus">${options(paymentStatuses,r.payment_status)}</select></label>
          <label>Payment method<input id="flPaymentMethod" value="${escFl(r.payment_method)}"></label>
          <label>Payment reference<input id="flPaymentRef" value="${escFl(r.payment_reference)}"></label>
          <label>Payment date<input id="flPaymentDate" type="date" value="${escFl(r.payment_date)}"></label>
        </div>
        <button type="button" class="btn btn-secondary" id="flPaystack">Pay online with Paystack</button>

        <h3>Funding readiness</h3>
        <div class="fl-docs">
          <label><input id="flBusinessPlan" type="checkbox" ${checked("business_plan")}>Business plan</label>
          <label><input id="flCashFlow" type="checkbox" ${checked("cash_flow")}>Cash flow</label>
          <label><input id="flPitchDeck" type="checkbox" ${checked("pitch_deck")}>Pitch deck</label>
          <label><input id="flCompanyReg" type="checkbox" ${checked("company_registration")}>Company registration</label>
          <label><input id="flTax" type="checkbox" ${checked("tax_status")}>Tax compliance</label>
          <label><input id="flBank" type="checkbox" ${checked("bank_account")}>Business bank account</label>
        </div>
        <div class="form-grid">
          <label>Funding status<select id="flFundingStatus">${options(fundingStatuses,r.funding_status)}</select></label>
          <label>Amount required<input id="flAmount" type="number" min="0" step="0.01" value="${escFl(r.funding_amount_required)}"></label>
          <label>Funding purpose<input id="flPurpose" value="${escFl(r.funding_purpose)}"></label>
          <label>Funder<input id="flFunder" value="${escFl(r.funder_name)}"></label>
          <label>Funder application reference<input id="flFunderRef" value="${escFl(r.funder_application_reference)}"></label>
          <label>Submission date<input id="flSubmitted" type="date" value="${escFl(r.submission_date)}"></label>
          <label>Decision date<input id="flDecision" type="date" value="${escFl(r.decision_date)}"></label>
          <label>Follow-up date<input id="flFollow" type="date" value="${escFl(r.follow_up_date)}"></label>
          <label class="full">Outstanding documents<textarea id="flOutstanding" rows="3">${escFl(r.outstanding_documents)}</textarea></label>
        </div>

        <h3>Business launch</h3>
        <div class="form-grid">
          <label>Launch status<select id="flLaunchStatus">${options(launchStatuses,r.launch_status)}</select></label>
          <label>Launch readiness score<input id="flLaunchScore" type="number" min="0" max="100" value="${r.launch_readiness_score}"></label>
          <label>Next action<input id="flNextAction" value="${escFl(r.next_action)}"></label>
          <label>Target launch date<input id="flTargetDate" type="date" value="${escFl(r.target_launch_date)}"></label>
          <label class="full">Internal notes<textarea id="flNotes" rows="6">${escFl(r.internal_notes)}</textarea></label>
        </div>

        <div class="form-actions"><button type="button" class="btn btn-secondary" onclick="closeDrawer()">Cancel</button><button class="btn btn-primary">Save integrated record</button></div>
      </form>`;

    openDrawer();

    document.getElementById("flPaystack").onclick = async () => {
      const response = await fetch("/api/payments/paystack/initialize", {
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({entity_type:"funding_service",entity_id:r.id,payer_email:r.email,payer_name:r.business_name||r.applicant_name})
      });
      const data = await response.json();
      if (!response.ok) return alert(data.detail || "Paystack initialization failed");
      window.open(data.authorization_url,"_blank","noopener");
    };

    document.getElementById("flClientForm").onsubmit = async event => {
      event.preventDefault();
      const serviceStatus = document.getElementById("flServiceStatus").value;
      const paymentStatus = document.getElementById("flPaymentStatus").value;
      if (["Assessment in progress","Ready to commence","Work in progress","Completed"].includes(serviceStatus) && paymentStatus!=="Paid") {
        if (!confirm("This paid service is not marked Paid. Save without commencing paid work?")) return;
      }

      await flApi(`/admin/funding-services/${id}`,{
        method:"PATCH",
        body:JSON.stringify({
          agristart_reference:document.getElementById("flAgriRef").value||null,
          entrepreneur_application_id:document.getElementById("flAgriId").value?Number(document.getElementById("flAgriId").value):null,
          service_status:serviceStatus,
          assigned_to_id:document.getElementById("flAssigned").value?Number(document.getElementById("flAssigned").value):null,
          payment_status:paymentStatus,
          payment_method:document.getElementById("flPaymentMethod").value||null,
          payment_reference:document.getElementById("flPaymentRef").value||null,
          payment_date:document.getElementById("flPaymentDate").value||null,
          funding_status:document.getElementById("flFundingStatus").value,
          funding_amount_required:document.getElementById("flAmount").value?Number(document.getElementById("flAmount").value):null,
          funding_purpose:document.getElementById("flPurpose").value||null,
          funder_name:document.getElementById("flFunder").value||null,
          funder_application_reference:document.getElementById("flFunderRef").value||null,
          submission_date:document.getElementById("flSubmitted").value||null,
          decision_date:document.getElementById("flDecision").value||null,
          follow_up_date:document.getElementById("flFollow").value||null,
          outstanding_documents:document.getElementById("flOutstanding").value||null,
          business_plan:document.getElementById("flBusinessPlan").checked,
          cash_flow:document.getElementById("flCashFlow").checked,
          pitch_deck:document.getElementById("flPitchDeck").checked,
          company_registration:document.getElementById("flCompanyReg").checked,
          tax_status:document.getElementById("flTax").checked,
          bank_account:document.getElementById("flBank").checked,
          launch_status:document.getElementById("flLaunchStatus").value,
          launch_readiness_score:Number(document.getElementById("flLaunchScore").value||0),
          next_action:document.getElementById("flNextAction").value||null,
          target_launch_date:document.getElementById("flTargetDate").value||null,
          internal_notes:document.getElementById("flNotes").value||null
        })
      });
      toast("Funding client saved");
      closeDrawer();
      loadFundingClients();
    };
  };

  document.addEventListener("DOMContentLoaded",()=>{
    ensureFundingView();
    if (typeof window.showView==="function" && !window.__flFundingViewWrapped) {
      const original = window.showView;
      window.showView = async name => {
        ensureFundingView();
        if (name!==VIEW) return original(name);
        document.querySelectorAll("#nav button").forEach(button=>button.classList.toggle("active",button.dataset.view===VIEW));
        document.querySelectorAll(".view").forEach(view=>view.classList.toggle("active",view.id===VIEW));
        const title=document.getElementById("pageTitle"); if(title) title.textContent="Funding Service Clients";
        return loadFundingClients();
      };
      window.__flFundingViewWrapped=true;
    }
  });
})();
