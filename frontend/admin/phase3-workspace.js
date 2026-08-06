/* FarmLink AgriStart Phase 3 administration */
(() => {
  const VIEW = "phase3centre";
  const businessStages = ["Idea stage","Validation","Business planning","Funding readiness","Pre-launch","Operating","Growth"];
  const documentTypes = ["ID Document","CIPC Registration","Tax Compliance","B-BEE Affidavit","Bank Confirmation Letter","Business Plan","Cash-flow Projection","Pitch Deck","Company Profile","Proof of Address","Supplier Quotation","Funding Application","Financial Statements"];
  const reviewStatuses = ["Pending review","Approved","Correction required","Rejected"];

  const p3Esc = value => String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
  const p3Options = (items,current)=>items.map(item=>`<option ${item===current?"selected":""}>${item}</option>`).join("");

  async function p3Api(path, options={}) {
    if (typeof api === "function") return api(path,options);
    const token=localStorage.getItem("farmlink_token")||"";
    const response=await fetch(`/api${path}`,{...options,headers:{"Content-Type":"application/json","Authorization":`Bearer ${token}`,...(options.headers||{})}});
    const data=await response.json();
    if(!response.ok) throw new Error(data.detail||"Request failed");
    return data;
  }

  function ensureView() {
    const nav=document.getElementById("nav");
    if(nav&&!nav.querySelector(`[data-view="${VIEW}"]`)){
      const button=document.createElement("button");
      button.dataset.view=VIEW;
      button.innerHTML="<span>P3</span>Business Workspace";
      const funding=nav.querySelector('[data-view="fundingclients"]')||nav.querySelector('[data-view="fundingcentre"]');
      if(funding) funding.insertAdjacentElement("afterend",button); else nav.appendChild(button);
      button.onclick=()=>window.showView(VIEW);
    }
    const host=document.querySelector("main")||document.getElementById("content")||document.getElementById("app");
    if(host&&!document.getElementById(VIEW)){
      const section=document.createElement("section");section.id=VIEW;section.className="view";host.appendChild(section);
    }
  }

  async function loadPhase3() {
    const view=document.getElementById(VIEW);
    view.innerHTML=`<div class="page-head"><div><span class="kicker">AgriStart Phase 3</span><h2>Business Workspace & Document Centre</h2><p class="muted">Commercial readiness, documents, mentorship, funding, launch and supplier verification in one operational workspace.</p></div><div class="toolbar"><input id="p3Search" placeholder="Search applicants"><select id="p3Filter"><option value="all">All readiness levels</option><option value="low">Below 40%</option><option value="medium">40% to 79%</option><option value="high">80% and above</option></select></div></div><div id="p3Stats" class="p3-stats"></div><div class="panel"><div id="p3Table"></div></div>`;

    const data=await p3Api("/admin/phase3/dashboard");
    const s=data.summary;
    document.getElementById("p3Stats").innerHTML=[
      ["Businesses",s.total,"Phase 3 pipeline"],["Average readiness",`${s.average_readiness}%`,"Portfolio score"],["Funding ready",s.funding_ready,"Ready for applications"],["Launch ready",s.launch_ready,"Prepared to operate"],["Verified suppliers",s.verified_suppliers,"Marketplace eligible"]
    ].map(([a,b,c])=>`<article><span>${a}</span><strong>${b}</strong><small>${c}</small></article>`).join("");

    const render=()=>{
      const q=document.getElementById("p3Search").value.toLowerCase();
      const filter=document.getElementById("p3Filter").value;
      const rows=data.items.filter(item=>{
        const match=!q||[item.full_name,item.reference,item.business_name,item.agricultural_interest,item.province].join(" ").toLowerCase().includes(q);
        const score=item.readiness_score;
        const range=filter==="all"||(filter==="low"&&score<40)||(filter==="medium"&&score>=40&&score<80)||(filter==="high"&&score>=80);
        return match&&range;
      });
      document.getElementById("p3Table").innerHTML=rows.length?`<div class="p3-table-wrap"><table class="table"><thead><tr><th>Applicant</th><th>Business stage</th><th>Readiness</th><th>Funding</th><th>Launch</th><th>Supplier</th><th>Next action</th><th></th></tr></thead><tbody>${rows.map(r=>`<tr><td><strong>${p3Esc(r.full_name)}</strong><div class="ref">${p3Esc(r.reference)}</div><small>${p3Esc(r.agricultural_interest)}</small></td><td>${p3Esc(r.business_stage)}</td><td><div class="p3-progress"><i style="width:${r.readiness_score}%"></i></div><small>${r.readiness_score}%</small></td><td>${p3Esc(r.funding_status)}</td><td>${p3Esc(r.launch_status)}</td><td>${p3Esc(r.supplier_verification_status)}</td><td>${p3Esc(r.next_action)}</td><td><button onclick="openPhase3Workspace(${r.id})">Open</button></td></tr>`).join("")}</tbody></table></div>`:`<div class="empty">No Phase 3 businesses match the filters.</div>`;
    };
    document.getElementById("p3Search").oninput=render;document.getElementById("p3Filter").onchange=render;render();
  }

  window.openPhase3Workspace=async id=>{
    const [data,users]=await Promise.all([p3Api(`/admin/phase3/entrepreneurs/${id}`),p3Api("/admin/users")]);
    const w=data.workspace,r=data.readiness,a=data.applicant;
    document.getElementById("drawerBody").innerHTML=`
      <span class="kicker">Phase 3 workspace</span><h2>${p3Esc(a.full_name)}</h2><p class="ref">${p3Esc(a.reference)}</p>
      <div class="p3-summary"><article><span>Readiness</span><strong>${r.overall}%</strong><small>Overall activation score</small></article><article><span>Documents</span><strong>${r.documents}/45</strong><small>Approved compliance file</small></article><article><span>Funding</span><strong>${p3Esc(w.funding_status)}</strong><small>${p3Esc(w.next_action)}</small></article><article><span>Launch</span><strong>${p3Esc(w.launch_status)}</strong><small>${p3Esc(w.marketplace_status)}</small></article></div>
      <div class="p3-tabs"><button class="active" data-p3tab="profile">Business</button><button data-p3tab="documents">Documents</button><button data-p3tab="tasks">Tasks</button><button data-p3tab="mentor">Mentorship</button></div>
      <form id="p3WorkspaceForm" class="p3-tab-panel active" data-p3panel="profile"><div class="form-grid">
        <label>Business name<input id="p3BusinessName" value="${p3Esc(w.business_name)}"></label>
        <label>Business stage<select id="p3BusinessStage">${p3Options(businessStages,w.business_stage)}</select></label>
        <label>Funding status<input id="p3FundingStatus" value="${p3Esc(w.funding_status)}"></label>
        <label>Launch status<input id="p3LaunchStatus" value="${p3Esc(w.launch_status)}"></label>
        <label>Marketplace status<input id="p3MarketplaceStatus" value="${p3Esc(w.marketplace_status)}"></label>
        <label>Supplier verification<select id="p3SupplierStatus">${p3Options(["Not verified","Verification pending","Verified","Rejected"],w.supplier_verification_status)}</select></label>
        <label>Assigned mentor<select id="p3Mentor"><option value="">Unassigned</option>${users.filter(u=>u.is_active).map(u=>`<option value="${u.id}" ${u.id===w.assigned_mentor_id?"selected":""}>${p3Esc(u.full_name)}</option>`).join("")}</select></label>
        <label>Target launch date<input id="p3TargetDate" type="date" value="${p3Esc(w.target_launch_date)}"></label>
        <label>Employees<input id="p3Employees" type="number" min="0" value="${w.employees_count||0}"></label>
        <label>Monthly turnover<input id="p3Turnover" type="number" min="0" value="${p3Esc(w.monthly_turnover)}"></label>
        <label class="full">Next action<input id="p3NextAction" value="${p3Esc(w.next_action)}"></label>
        <label class="full">Internal notes<textarea id="p3Notes" rows="6">${p3Esc(w.internal_notes)}</textarea></label>
      </div><div class="form-actions"><button type="button" class="btn btn-secondary" onclick="closeDrawer()">Cancel</button><button class="btn btn-primary">Save workspace</button></div></form>

      <section class="p3-tab-panel" data-p3panel="documents"><div class="p3-section-head"><h3>Document Centre</h3><button class="btn btn-secondary" id="p3UploadButton">Upload document</button></div><div class="p3-document-list">${data.documents.length?data.documents.map(doc=>`<article><div><strong>${p3Esc(doc.document_type)}</strong><span>${p3Esc(doc.filename)} - ${(doc.file_size/1024).toFixed(1)} KB</span></div><div><b>${p3Esc(doc.review_status)}</b><a href="${doc.download_url}" target="_blank">Download</a><button data-review-doc="${doc.id}">Review</button></div></article>`).join(""):`<p class="muted">No documents uploaded.</p>`}</div></section>
      <section class="p3-tab-panel" data-p3panel="tasks"><div class="p3-section-head"><h3>Action Tasks</h3><button class="btn btn-secondary" id="p3AddTask">Add task</button></div><div class="p3-card-list">${data.tasks.length?data.tasks.map(task=>`<article><strong>${p3Esc(task.title)}</strong><span>${p3Esc(task.category)} - ${p3Esc(task.priority)}</span><p>${p3Esc(task.description)}</p><small>${p3Esc(task.status)}${task.due_date?` - Due ${task.due_date}`:""}</small></article>`).join(""):`<p class="muted">No tasks assigned.</p>`}</div></section>
      <section class="p3-tab-panel" data-p3panel="mentor"><div class="p3-section-head"><h3>Mentorship</h3><button class="btn btn-secondary" id="p3AddSession">Schedule session</button></div><div class="p3-card-list">${data.mentor_sessions.length?data.mentor_sessions.map(s=>`<article><strong>${p3Esc(s.session_type)}</strong><span>${new Date(s.session_date).toLocaleString("en-ZA")}</span><p>${p3Esc(s.objectives)}</p><small>${p3Esc(s.status)}${s.score!=null?` - Score ${s.score}%`:""}</small></article>`).join(""):`<p class="muted">No mentor sessions recorded.</p>`}</div></section>`;

    openDrawer();
    document.querySelectorAll("[data-p3tab]").forEach(btn=>btn.onclick=()=>{document.querySelectorAll("[data-p3tab]").forEach(x=>x.classList.toggle("active",x===btn));document.querySelectorAll("[data-p3panel]").forEach(x=>x.classList.toggle("active",x.dataset.p3panel===btn.dataset.p3tab));});

    document.getElementById("p3WorkspaceForm").onsubmit=async e=>{e.preventDefault();await p3Api(`/admin/phase3/entrepreneurs/${id}/workspace`,{method:"PATCH",body:JSON.stringify({business_name:document.getElementById("p3BusinessName").value||null,business_stage:document.getElementById("p3BusinessStage").value,funding_status:document.getElementById("p3FundingStatus").value,launch_status:document.getElementById("p3LaunchStatus").value,marketplace_status:document.getElementById("p3MarketplaceStatus").value,supplier_verification_status:document.getElementById("p3SupplierStatus").value,assigned_mentor_id:document.getElementById("p3Mentor").value?Number(document.getElementById("p3Mentor").value):null,target_launch_date:document.getElementById("p3TargetDate").value||null,employees_count:Number(document.getElementById("p3Employees").value||0),monthly_turnover:document.getElementById("p3Turnover").value?Number(document.getElementById("p3Turnover").value):null,next_action:document.getElementById("p3NextAction").value||null,internal_notes:document.getElementById("p3Notes").value||null})});toast("Phase 3 workspace saved");closeDrawer();loadPhase3();};

    document.getElementById("p3UploadButton").onclick=async()=>{const type=prompt(`Document type:\n${documentTypes.join("\n")}`);if(!documentTypes.includes(type))return alert("Select an exact supported document type.");const input=document.createElement("input");input.type="file";input.accept=".pdf,.jpg,.jpeg,.png,.docx,.xlsx";input.onchange=async()=>{const fd=new FormData();fd.append("document_type",type);fd.append("file",input.files[0]);const token=localStorage.getItem("farmlink_token")||"";const response=await fetch(`/api/admin/phase3/entrepreneurs/${id}/documents`,{method:"POST",headers:{"Authorization":`Bearer ${token}`},body:fd});const result=await response.json();if(!response.ok)return alert(result.detail||"Upload failed");toast("Document uploaded");openPhase3Workspace(id);};input.click();};

    document.querySelectorAll("[data-review-doc]").forEach(btn=>btn.onclick=async()=>{const status=prompt(`Review status:\n${reviewStatuses.join("\n")}`,"Approved");if(!reviewStatuses.includes(status))return;const comment=prompt("Reviewer comment","")||"";await p3Api(`/admin/phase3/documents/${btn.dataset.reviewDoc}/review?review_status=${encodeURIComponent(status)}&reviewer_comment=${encodeURIComponent(comment)}`,{method:"PATCH"});toast("Document review saved");openPhase3Workspace(id);});
    document.getElementById("p3AddTask").onclick=async()=>{const title=prompt("Task title");if(!title)return;const description=prompt("Task description","")||"";const due=prompt("Due date (YYYY-MM-DD)","")||null;await p3Api(`/admin/phase3/entrepreneurs/${id}/tasks`,{method:"POST",body:JSON.stringify({title,description,due_date:due})});toast("Task added");openPhase3Workspace(id);};
    document.getElementById("p3AddSession").onclick=async()=>{const date=prompt("Session date and time (YYYY-MM-DDTHH:MM)",new Date().toISOString().slice(0,16));if(!date)return;const objectives=prompt("Session objectives","")||"";await p3Api(`/admin/phase3/entrepreneurs/${id}/mentor-sessions`,{method:"POST",body:JSON.stringify({mentor_id:w.assigned_mentor_id,session_date:date,objectives})});toast("Mentor session scheduled");openPhase3Workspace(id);};
  };

  document.addEventListener("DOMContentLoaded",()=>{ensureView();if(typeof window.showView==="function"&&!window.__p3Wrapped){const original=window.showView;window.showView=async name=>{ensureView();if(name!==VIEW)return original(name);document.querySelectorAll("#nav button").forEach(b=>b.classList.toggle("active",b.dataset.view===VIEW));document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active",v.id===VIEW));const title=document.getElementById("pageTitle");if(title)title.textContent="Business Workspace & Document Centre";return loadPhase3();};window.__p3Wrapped=true;}});
})();
