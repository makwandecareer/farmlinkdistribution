/* FarmLink AgriStart Phase 4 administration */
(() => {
  const VIEW = "phase4centre";
  const esc4 = value => String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
  const money4 = value => value == null ? "On request" : `R ${Number(value).toLocaleString("en-ZA",{minimumFractionDigits:2,maximumFractionDigits:2})}`;

  async function api4(path, options={}) {
    if (typeof api === "function") return api(path, options);
    const token=localStorage.getItem("farmlink_token")||"";
    const response=await fetch(`/api${path}`,{...options,headers:{"Content-Type":"application/json","Authorization":`Bearer ${token}`,...(options.headers||{})}});
    const data=await response.json();
    if(!response.ok) throw new Error(data.detail||"Request failed");
    return data;
  }

  function ensureView() {
    const nav=document.getElementById("nav");
    if(nav&&!nav.querySelector(`[data-view="${VIEW}"]`)){
      const button=document.createElement("button");button.dataset.view=VIEW;button.innerHTML="<span>P4</span>Supplier Activation";
      const p3=nav.querySelector('[data-view="phase3centre"]');if(p3)p3.insertAdjacentElement("afterend",button);else nav.appendChild(button);
      button.onclick=()=>window.showView(VIEW);
    }
    const host=document.querySelector("main")||document.getElementById("content")||document.getElementById("app");
    if(host&&!document.getElementById(VIEW)){const section=document.createElement("section");section.id=VIEW;section.className="view";host.appendChild(section);}
  }

  async function loadPhase4() {
    const view=document.getElementById(VIEW);
    view.innerHTML=`
      <div class="page-head"><div><span class="kicker">AgriStart Phase 4</span><h2>Supplier Activation & Buyer Matching</h2><p class="muted">Verify businesses, activate farmer records, publish marketplace listings and match suppliers to real buyer requirements.</p></div><div class="toolbar"><button class="btn btn-primary" id="p4RunMatching">Run smart matching</button></div></div>
      <div id="p4Stats" class="p4-stats"></div>
      <div class="p4-tabs"><button class="active" data-p4tab="activation">Activation</button><button data-p4tab="requirements">Buyer requirements</button><button data-p4tab="matches">Matches</button><button data-p4tab="listings">Marketplace</button></div>
      <section class="p4-panel active" data-p4panel="activation"><div id="p4Activation"></div></section>
      <section class="p4-panel" data-p4panel="requirements"><div class="p4-section-head"><h3>Buyer requirements</h3><button class="btn btn-secondary" id="p4AddRequirement">Add requirement</button></div><div id="p4Requirements"></div></section>
      <section class="p4-panel" data-p4panel="matches"><div id="p4Matches"></div></section>
      <section class="p4-panel" data-p4panel="listings"><div class="p4-section-head"><h3>Marketplace listings</h3><button class="btn btn-secondary" id="p4AddListing">Add listing</button></div><div id="p4Listings"></div></section>`;

    document.querySelectorAll("[data-p4tab]").forEach(btn=>btn.onclick=()=>{document.querySelectorAll("[data-p4tab]").forEach(x=>x.classList.toggle("active",x===btn));document.querySelectorAll("[data-p4panel]").forEach(x=>x.classList.toggle("active",x.dataset.p4panel===btn.dataset.p4tab));});

    const dashboard=await api4("/admin/phase4/dashboard");
    const s=dashboard.summary;
    document.getElementById("p4Stats").innerHTML=[["Candidates",s.candidates,"AgriStart businesses"],["Verified",s.verified,"Supplier checks complete"],["Activated",s.activated,"Farmer records created"],["Published",s.published_listings,"Marketplace listings"],["Open buyer needs",s.open_requirements,"Demand opportunities"],["Active matches",s.active_matches,"Buyer-supplier pipeline"]].map(([a,b,c])=>`<article><span>${a}</span><strong>${b}</strong><small>${c}</small></article>`).join("");

    document.getElementById("p4Activation").innerHTML=`<div class="p4-table-wrap"><table class="table"><thead><tr><th>Business</th><th>Phase 3</th><th>Verification</th><th>Activation</th><th>Listings</th><th>Matches</th><th></th></tr></thead><tbody>${dashboard.items.map(r=>`<tr><td><strong>${esc4(r.workspace?.business_name||r.full_name)}</strong><div class="ref">${esc4(r.reference)}</div><small>${esc4(r.agricultural_interest)}</small></td><td>${esc4(r.workspace?.launch_status||"Not started")}</td><td>${esc4(r.activation.verification_status)}</td><td>${r.farmer?`<strong>${esc4(r.farmer.reference)}</strong>`:esc4(r.activation.activation_status)}</td><td>${r.listing_count}</td><td>${r.match_count}</td><td><button onclick="openP4Activation(${r.entrepreneur_id})">Manage</button></td></tr>`).join("")}</tbody></table></div>`;

    const requirements=await api4("/admin/phase4/buyer-requirements");
    document.getElementById("p4Requirements").innerHTML=requirements.length?`<div class="p4-card-grid">${requirements.map(r=>`<article><span class="ref">${esc4(r.reference)}</span><h3>${esc4(r.product_category)}</h3><strong>${esc4(r.buyer?.business_name)}</strong><p>${esc4(r.product_description)}</p><small>${esc4(r.location)} - ${esc4(r.quantity_required)} - ${esc4(r.status)}</small></article>`).join("")}</div>`:`<p class="empty">No buyer requirements recorded.</p>`;

    const matches=await api4("/admin/phase4/matches");
    document.getElementById("p4Matches").innerHTML=matches.length?`<div class="p4-table-wrap"><table class="table"><thead><tr><th>Supplier</th><th>Buyer</th><th>Requirement</th><th>Score</th><th>Reasons</th><th>Status</th><th></th></tr></thead><tbody>${matches.map(m=>`<tr><td>${esc4(m.supplier_name)}</td><td>${esc4(m.buyer?.business_name)}</td><td>${esc4(m.requirement?.product_category)}</td><td><strong>${m.match_score}%</strong></td><td>${esc4(m.match_reasons)}</td><td>${esc4(m.status)}</td><td><button onclick="updateP4Match(${m.id},'${esc4(m.status)}')">Update</button></td></tr>`).join("")}</tbody></table></div>`:`<p class="empty">Run smart matching after publishing listings and buyer requirements.</p>`;

    const listings=await api4("/admin/phase4/listings");
    document.getElementById("p4Listings").innerHTML=listings.length?`<div class="p4-card-grid">${listings.map(l=>`<article><span class="ref">${esc4(l.reference)}</span><h3>${esc4(l.product_name)}</h3><strong>${esc4(l.business_name)}</strong><p>${esc4(l.description)}</p><small>${esc4(l.location)} - ${l.weekly_capacity} weekly - ${money4(l.unit_price)} - ${esc4(l.status)}</small></article>`).join("")}</div>`:`<p class="empty">No marketplace listings created.</p>`;

    document.getElementById("p4RunMatching").onclick=async()=>{const result=await api4("/admin/phase4/matching/run?minimum_score=40",{method:"POST"});toast(`Matching complete: ${result.created} created, ${result.updated} updated`);loadPhase4();};
    document.getElementById("p4AddRequirement").onclick=()=>createRequirement();
    document.getElementById("p4AddListing").onclick=()=>createListing(dashboard.items);
  }

  window.openP4Activation=async id=>{
    const data=await api4(`/admin/phase4/entrepreneurs/${id}`);const a=data.activation,w=data.workspace||{},farmer=data.farmer;
    document.getElementById("drawerBody").innerHTML=`
      <span class="kicker">Supplier activation</span><h2>${esc4(w.business_name||data.full_name)}</h2><p class="ref">${esc4(data.reference)}</p>
      <div class="p4-summary"><article><span>Verification</span><strong>${esc4(a.verification_status)}</strong></article><article><span>Activation</span><strong>${esc4(a.activation_status)}</strong></article><article><span>Farmer record</span><strong>${esc4(farmer?.reference||"Not created")}</strong></article><article><span>Marketplace</span><strong>${a.marketplace_enabled?"Enabled":"Disabled"}</strong></article></div>
      <form id="p4ActivationForm"><div class="form-grid">
        <label>Verification status<select id="p4Verify">${["Not verified","Verification pending","Verified","Rejected"].map(x=>`<option ${x===a.verification_status?"selected":""}>${x}</option>`).join("")}</select></label>
        <label>Activation status<select id="p4ActivationStatus">${["Not started","In review","Ready for activation","Activated","Suspended"].map(x=>`<option ${x===a.activation_status?"selected":""}>${x}</option>`).join("")}</select></label>
        <label>Marketplace enabled<input id="p4MarketplaceEnabled" type="checkbox" ${a.marketplace_enabled?"checked":""}></label>
        <label>Buyer matching enabled<input id="p4MatchingEnabled" type="checkbox" ${a.buyer_matching_enabled?"checked":""}></label>
        <label class="full">Verification notes<textarea id="p4VerificationNotes" rows="5">${esc4(a.verification_notes)}</textarea></label>
      </div><div class="form-actions"><button class="btn btn-primary">Save verification</button>${farmer?"":`<button type="button" class="btn btn-secondary" id="p4ConvertFarmer">Activate as farmer</button>`}</div></form>`;
    openDrawer();
    document.getElementById("p4ActivationForm").onsubmit=async e=>{e.preventDefault();await api4(`/admin/phase4/entrepreneurs/${id}/activation`,{method:"PATCH",body:JSON.stringify({verification_status:document.getElementById("p4Verify").value,activation_status:document.getElementById("p4ActivationStatus").value,verification_notes:document.getElementById("p4VerificationNotes").value||null,marketplace_enabled:document.getElementById("p4MarketplaceEnabled").checked,buyer_matching_enabled:document.getElementById("p4MatchingEnabled").checked})});toast("Supplier activation saved");openP4Activation(id);};
    document.getElementById("p4ConvertFarmer")?.addEventListener("click",async()=>{const farmName=prompt("Farm or business name",w.business_name||data.full_name);if(!farmName)return;const producerType=prompt("Producer type",data.agricultural_interest||"Agricultural supplier");if(!producerType)return;const capacity=Number(prompt("Weekly capacity","0")||0);const eggSizes=prompt("Products, grades or sizes",data.agricultural_interest||"Not specified");if(!eggSizes)return;const packaging=prompt("Packaging","")||null;const delivery=prompt("Delivery capability","No - collection only");if(!delivery)return;await api4(`/admin/phase4/entrepreneurs/${id}/convert-to-farmer`,{method:"POST",body:JSON.stringify({farm_name:farmName,location:`${data.municipality}, ${data.province}`,producer_type:producerType,weekly_capacity:capacity,egg_sizes:eggSizes,packaging,delivery_capability:delivery,notes:`Activated from AgriStart ${data.reference}`})});toast("Entrepreneur activated as farmer");openP4Activation(id);});
  };

  window.updateP4Match=async(id,current)=>{const status=prompt("Match status",current||"Suggested");if(!status)return;const notes=prompt("Introduction notes","")||null;await api4(`/admin/phase4/matches/${id}`,{method:"PATCH",body:JSON.stringify({status,introduction_notes:notes})});toast("Match updated");loadPhase4();};

  async function createRequirement(){const buyers=await api4("/admin/buyers?status=Approved");if(!buyers.items.length)return alert("No approved buyers available.");const buyerId=Number(prompt(`Buyer ID:\n${buyers.items.map(b=>`${b.id} - ${b.business_name}`).join("\n")}`));if(!buyerId)return;const category=prompt("Product category");if(!category)return;const description=prompt("Product description");if(!description)return;const location=prompt("Required location or delivery area");if(!location)return;const quantity=prompt("Quantity required");if(!quantity)return;const capacity=Number(prompt("Minimum weekly capacity","0")||0);const packaging=prompt("Packaging required","")||null;const delivery=confirm("Is supplier delivery required?");await api4("/admin/phase4/buyer-requirements",{method:"POST",body:JSON.stringify({buyer_id:buyerId,product_category:category,product_description:description,location,quantity_required:quantity,minimum_weekly_capacity:capacity,packaging_required:packaging,delivery_required:delivery})});toast("Buyer requirement created");loadPhase4();}

  async function createListing(items){const eligible=items.filter(x=>x.farmer&&x.activation.verification_status==="Verified");if(!eligible.length)return alert("No verified activated suppliers available.");const entrepreneurId=Number(prompt(`Entrepreneur ID:\n${eligible.map(x=>`${x.entrepreneur_id} - ${x.workspace?.business_name||x.full_name}`).join("\n")}`));if(!entrepreneurId)return;const item=eligible.find(x=>x.entrepreneur_id===entrepreneurId);const product=prompt("Product name",item.agricultural_interest||"");if(!product)return;const category=prompt("Product category",item.agricultural_interest||"Agriculture");if(!category)return;const description=prompt("Marketplace description",item.business_idea||"");if(!description)return;const capacity=Number(prompt("Weekly capacity",String(item.farmer.weekly_capacity||0))||0);const packaging=prompt("Packaging",item.farmer.packaging||"")||null;const delivery=prompt("Delivery capability",item.farmer.delivery_capability||"");if(!delivery)return;const minimum=prompt("Minimum order","")||null;const priceRaw=prompt("Unit price (leave blank for on request)","");const status=confirm("Publish immediately?")?"Published":"Draft";await api4("/admin/phase4/listings",{method:"POST",body:JSON.stringify({entrepreneur_id:entrepreneurId,product_name:product,product_category:category,description,location:item.farmer.location,weekly_capacity:capacity,packaging,delivery_capability:delivery,minimum_order:minimum,unit_price:priceRaw?Number(priceRaw):null,status})});toast("Marketplace listing created");loadPhase4();}

  document.addEventListener("DOMContentLoaded",()=>{ensureView();if(typeof window.showView==="function"&&!window.__p4Wrapped){const original=window.showView;window.showView=async name=>{ensureView();if(name!==VIEW)return original(name);document.querySelectorAll("#nav button").forEach(b=>b.classList.toggle("active",b.dataset.view===VIEW));document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active",v.id===VIEW));const title=document.getElementById("pageTitle");if(title)title.textContent="Supplier Activation & Buyer Matching";return loadPhase4();};window.__p4Wrapped=true;}});
})();
