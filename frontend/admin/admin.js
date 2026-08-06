/* FARMLINK_SAFE_INSERT_BEFORE_V1
   Prevents repeated table-enhancement observers from calling insertBefore
   with a reference node that has already moved to another parent. */
(() => {
  if (window.__farmLinkSafeInsertBeforeInstalled) return;
  window.__farmLinkSafeInsertBeforeInstalled = true;

  const nativeInsertBefore = Node.prototype.insertBefore;
  Node.prototype.insertBefore = function(newNode, referenceNode) {
    if (referenceNode == null) {
      return nativeInsertBefore.call(this, newNode, null);
    }

    if (referenceNode.parentNode !== this) {
      return this.appendChild(newNode);
    }

    return nativeInsertBefore.call(this, newNode, referenceNode);
  };
})();
const API=(()=>{const c=window.FARMLINK_API_URL?.trim();if(c)return c.replace(/\/$/,'')+'/api';if(['localhost','127.0.0.1'].includes(location.hostname))return'http://localhost:8000/api';return'https://farmlinkdistribution.onrender.com/api'})();
let token=localStorage.getItem('farmlink_token')||'',currentUser=null;
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??'\u2014').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const fmtMoney=v=>new Intl.NumberFormat('en-ZA',{style:'currency',currency:'ZAR'}).format(Number(v||0));
const fmtDate=v=>v?new Date(v).toLocaleDateString('en-ZA'):'\u2014';
function fmtAdminDate(value){
  if(!value)return 'Never';
  const d=new Date(value);
  return `${d.toLocaleDateString('en-ZA',{day:'2-digit',month:'short',year:'numeric'})}<div class="ref">${d.toLocaleTimeString('en-ZA',{hour:'2-digit',minute:'2-digit',hour12:false})} SAST</div>`;
}
function profileDetail(label,value){
  return `<div class="detail"><span>${esc(label)}</span><strong>${value===null||value===undefined||value===''?'\u2014':value}</strong></div>`;
}
function roleBadge(role){
  const value=String(role||'ADMIN').toUpperCase();
  const labels={CEO:'CEO',FINANCE:'Finance',OPERATIONS:'Operations',LOGISTICS:'Logistics',QUALITY:'Quality control',ADMIN:'Administrator'};
  return `<span class="role-badge role-${value.toLowerCase()}"><i></i>${labels[value]||value}</span>`;
}
const SA_PROVINCES=['Eastern Cape','Free State','Gauteng','KwaZulu-Natal','Limpopo','Mpumalanga','North West','Northern Cape','Western Cape'];
const provinceAliases={
  'EC':'Eastern Cape','EASTERN CAPE':'Eastern Cape',
  'FS':'Free State','FREE STATE':'Free State',
  'GP':'Gauteng','GAUTENG':'Gauteng',
  'KZN':'KwaZulu-Natal','KWAZULU NATAL':'KwaZulu-Natal','KWAZULU-NATAL':'KwaZulu-Natal',
  'LP':'Limpopo','LIMPOPO':'Limpopo',
  'MP':'Mpumalanga','MPUMALANGA':'Mpumalanga',
  'NW':'North West','NORTH WEST':'North West',
  'NC':'Northern Cape','NORTHERN CAPE':'Northern Cape',
  'WC':'Western Cape','WESTERN CAPE':'Western Cape'
};
function normalizeProvince(value){
  const raw=String(value||'').trim();
  if(!raw)return 'Not specified';
  const upper=raw.toUpperCase().replaceAll('.','').replace(/\s+/g,' ');
  if(provinceAliases[upper])return provinceAliases[upper];
  const found=SA_PROVINCES.find(p=>upper.includes(p.toUpperCase()));
  return found||raw;
}
function provinceOf(record){
  return normalizeProvince(record.province||record.location||record.physical_address||record.address);
}
function provinceOptions(selected='all'){
  return `<option value="all">All provinces</option>${SA_PROVINCES.map(p=>`<option ${selected===p?'selected':''}>${p}</option>`).join('')}`;
}
function provinceBadge(record){
  const p=provinceOf(record);
  return `<span class="province-chip">${esc(p)}</span>`;
}
const toast=(m,ok=true)=>{const t=$('#toast');t.textContent=m;t.style.background=ok?'#0d6547':'#a82e2e';t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3500)};
const headers=()=>({'Content-Type':'application/json',...(token?{'Authorization':`Bearer ${token}`}:{})});
const normalizedRole=()=>String(currentUser?.role||'').trim().toUpperCase();
const isCEO=()=>normalizedRole()==='CEO';
function requireCEO(){
  if(isCEO())return true;
  toast('Only the CEO account can manage administrators.',false);
  return false;
}

async function api(path,opts={}){const r=await fetch(API+path,{...opts,headers:{...headers(),...(opts.headers||{})}});if(r.status===401&&token){logout();throw new Error('Session expired')}const ct=r.headers.get('content-type')||'';const d=r.status===204?null:ct.includes('json')?await r.json():await r.text();if(!r.ok)throw new Error(d?.detail||d||'Request failed');return d}
function logout(){localStorage.removeItem('farmlink_token');token='';currentUser=null;$('#app').classList.add('hidden');$('#loginScreen').classList.remove('hidden')}
$('#logout').onclick=logout;
$('#loginForm').onsubmit=async e=>{e.preventDefault();$('#loginError').textContent='';try{const d=await api('/auth/login',{method:'POST',body:JSON.stringify({email:$('#loginEmail').value,password:$('#loginPassword').value})});token=d.access_token;localStorage.setItem('farmlink_token',token);currentUser=d.user;await start()}catch(err){$('#loginError').textContent=err.message}};
async function start(){try{currentUser=currentUser||await api('/auth/me');$('#loginScreen').classList.add('hidden');$('#app').classList.remove('hidden');$('#sideName').textContent=currentUser.full_name;$('#sideRole').textContent=currentUser.job_title;const initials=currentUser.full_name.split(' ').map(x=>x[0]).slice(0,2).join('');$('#avatar').textContent=initials;$('#topAvatar').textContent=initials;$('#topName').textContent=currentUser.full_name;$('#topRole').textContent=`${currentUser.job_title||'Administrator'} \u00B7 ${String(currentUser.role||'ADMIN').toUpperCase()}`;$('#usersNav').style.display=isCEO()?'flex':'none';if(currentUser.must_change_password)setTimeout(openPasswordModal,300);await showView('dashboard')}catch(e){logout()}}
const titles={dashboard:'Executive overview',farmers:'Farmer applications',buyers:'Business buyers',orders:'Bulk orders',memberships:'Memberships & marketing',inventory:'Inventory management',logistics:'Logistics & dispatch',quality:'Quality control',finance:'Finance centre',payments:'Payment records',notifications:'Communications',documents:'Document centre',users:'Administrator management',audit:'Audit trail',marketplace:'Marketplace control'};
$$('#nav button').forEach(b=>b.onclick=()=>showView(b.dataset.view));$('#refresh').onclick=()=>showView($('.view.active').id);
async function showView(name){$$('#nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===name));$$('.view').forEach(v=>v.classList.toggle('active',v.id===name));$('#pageTitle').textContent=titles[name]||name;const loaders={dashboard:loadDashboard,farmers:()=>loadResource('farmers'),buyers:()=>loadResource('buyers'),orders:()=>loadResource('orders'),memberships:()=>loadResource('memberships'),inventory:loadInventory,logistics:loadLogistics,quality:loadQuality,finance:loadFinance,payments:loadPayments,notifications:loadNotifications,documents:loadDocuments,users:loadUsers,audit:loadAudit,marketplace:loadMarketplace};try{await loaders[name]?.()}catch(e){toast(e.message,false)}}
const badge=s=>`<span class="status ${esc(String(s).replaceAll(' ','-'))}">${esc(s)}</span>`;
const empty=(m='No records available.',detail='New activity will appear here automatically.')=>`<div class="empty-state"><div><div class="empty-icon">\u2713</div><strong>${esc(m)}</strong><p>${esc(detail)}</p></div></div>`;
function bars(series){const max=Math.max(...series.map(x=>Number(x.value)),1);return `<div class="chart">${series.map(x=>`<div class="chart-col"><div class="chart-bar" style="height:${Math.max(4,Number(x.value)/max*180)}px" title="${esc(x.value)}"></div><span>${esc(x.label)}</span></div>`).join('')}</div>`}
async function loadDashboard(){const [d,a]=await Promise.all([api('/admin/dashboard'),api('/admin/analytics')]);const c=d.counts;$('#dashboard').innerHTML=`<div class="command-banner"><div><span class="kicker light">Operations command</span><h2>National distribution oversight from one accountable system.</h2><p>Monitor registrations, revenue, supply, fulfilment, quality and team activity in real time.</p></div><div class="command-date"><strong>${new Intl.DateTimeFormat('en-ZA',{dateStyle:'full'}).format(new Date())}</strong><span>Gauteng headquarters \u00B7 Nationwide coordination</span></div></div>
<div class="quick-actions"><button class="quick-action" onclick="showView('farmers')"><span class="qa-icon">\u00EF\u00BC\u2039</span><span><strong>Review farmers</strong><span>Supplier approvals</span></span></button><button class="quick-action" onclick="showView('buyers')"><span class="qa-icon">\u25A3</span><span><strong>Review buyers</strong><span>Customer onboarding</span></span></button><button class="quick-action" onclick="showView('orders')"><span class="qa-icon">\u25CE</span><span><strong>Manage orders</strong><span>Quotes and fulfilment</span></span></button><button class="quick-action" onclick="showView('finance')"><span class="qa-icon">R</span><span><strong>Create invoice</strong><span>Finance control</span></span></button><button class="quick-action" onclick="showView('logistics')"><span class="qa-icon">\u21C4</span><span><strong>Schedule dispatch</strong><span>Delivery planning</span></span></button></div><div class="metrics">${[['R','Today revenue',fmtMoney(a.today_revenue),'Verified payments'],['\u2197','Month revenue',fmtMoney(a.month_revenue),'Current calendar month'],['\u25CF','Eggs traded',Number(a.total_trays).toLocaleString('en-ZA')+' trays','Recorded order volume'],['\u2659','Active farmers',a.active_farmers,'Approved suppliers'],['\u2713','Delivery performance',a.delivery_performance+'%','Completed dispatches']].map(([i,l,v,s])=>`<article class="metric"><span class="metric-icon">${i}</span><span class="label">${l}</span><strong>${v}</strong><small>${s}</small></article>`).join('')}</div>
<div class="grid-2"><article class="panel"><div class="panel-head"><div><span class="kicker">Commercial performance</span><h3>Revenue trend</h3></div></div>${bars(a.revenue_series)}</article><article class="panel"><div class="panel-head"><div><span class="kicker">Buyer activity</span><h3>Top customers</h3></div></div><div class="rank-list">${a.top_buyers.length?a.top_buyers.map((x,i)=>`<div class="rank-item"><span class="rank-num">${i+1}</span><strong>${esc(x.name)}</strong><span>${x.orders} orders</span></div>`).join(''):empty()}</div></article></div>
<div class="grid-2" style="margin-top:18px"><article class="panel"><div class="panel-head"><div><span class="kicker">Order pipeline</span><h3>Latest submissions</h3></div></div>${d.latest.length?d.latest.map(x=>`<div class="list-item"><div><strong>${esc(nameOf(x))}</strong><div class="ref">${esc(x.reference)}</div></div><span>${esc(labelOf(x.type))}</span>${badge(x.status)}<button class="link-btn" onclick="openRecord('${plural(x.type)}',${x.id})">Review</button></div>`).join(''):empty()}</article><article class="panel"><div class="panel-head"><div><span class="kicker">Supplier strength</span><h3>Top capacity</h3></div></div><div class="rank-list">${a.top_suppliers.length?a.top_suppliers.map((x,i)=>`<div class="rank-item"><span class="rank-num">${i+1}</span><strong>${esc(x.name)}</strong><span>${Number(x.capacity).toLocaleString()} trays/wk</span></div>`).join(''):empty()}</div></article></div>`}
const plural=t=>t==='membership'?'memberships':t+'s',labelOf=t=>({farmer:'Farmer',buyer:'Buyer',order:'Order',membership:'Membership',entrepreneur:'AgriStart'})[t]||t,nameOf=r=>r.farm_name||r.business_name||r.payer_name||r.full_name||'Record';
const actionButtons=(resource,record)=>`<div class="row-actions"><button class="link-btn" onclick="openRecord('${resource}',${record.id})">Review</button><button class="approve-btn" onclick="quickDecision('${resource}',${record.id},'Approved')">Approve</button><button class="reject-btn" onclick="quickDecision('${resource}',${record.id},'Rejected')">Reject</button></div>`;
window.quickDecision=async(resource,id,status)=>{const verb=status==='Approved'?'approve':'reject';if(!confirm(`Are you sure you want to ${verb} this ${resource.slice(0,-1)} record?`))return;try{await api(`/admin/${resource}/${id}`,{method:'PATCH',body:JSON.stringify({status})});toast(`Record ${status.toLowerCase()}`);await loadResource(resource)}catch(err){toast(err.message,false)}};
const configs={farmers:{title:'Farmer applications',desc:'Verify supplier identity, capacity, location and delivery capability.',cols:['Supplier','Province','Location','Weekly capacity','Status','Assigned',''],row:r=>[`${esc(r.farm_name)}<div class="ref">${esc(r.reference)}</div>`,provinceBadge(r),esc(r.location),`${Number(r.weekly_capacity).toLocaleString()} trays`,badge(r.status),esc(r.assigned_to?.full_name||'Unassigned'),actionButtons('farmers',r)]},buyers:{title:'Business buyer registrations',desc:'Review commercial requirements and customer demand.',cols:['Buyer','Province','Category','Weekly demand','Status','Assigned',''],row:r=>[`${esc(r.business_name)}<div class="ref">${esc(r.reference)}</div>`,provinceBadge(r),esc(r.category),esc(r.weekly_volume),badge(r.status),esc(r.assigned_to?.full_name||'Unassigned'),actionButtons('buyers',r)]},orders:{title:'Bulk order requests',desc:'Confirm supply, quotations and fulfilment ownership.',cols:['Customer','Quantity','Required date','Status','Quoted',''],row:r=>[`${esc(r.business_name)}<div class="ref">${esc(r.reference)}</div>`,esc(r.quantity),fmtDate(r.required_date),badge(r.status),r.quoted_amount?fmtMoney(r.quoted_amount):'Not quoted',`<button class="link-btn" onclick="openRecord('orders',${r.id})">Manage</button>`]},memberships:{title:'Membership and marketing',desc:'Review premium subscriptions and campaign applications.',cols:['Applicant','Service','Location','Status','Assigned',''],row:r=>[`${esc(r.business_name)}<div class="ref">${esc(r.reference)}</div>`,esc(r.selected_service),esc(r.location),badge(r.status),esc(r.assigned_to?.full_name||'Unassigned'),`<button class="link-btn" onclick="openRecord('memberships',${r.id})">Review</button>`]},
 entrepreneurs:{title:'Agricultural entrepreneurship applications',desc:'Develop students, graduates and aspiring farmers into market-ready agricultural businesses.',cols:['Applicant','Qualification','Interest','Province','Status',''],row:r=>[`${r.full_name}<div class="ref">${r.reference}</div>`,r.qualification,r.agricultural_interest,r.province,badge(r.status),`<div class="row-actions"><button onclick="openRecord('entrepreneurs',${r.id})">Review</button></div>`]}};
async function loadResource(resource){const cfg=configs[resource],v=$('#'+resource);v.innerHTML=`<div class="page-head"><div><span class="kicker">Central records</span><h2>${cfg.title}</h2><p class="muted">${cfg.desc}</p></div><div class="toolbar"><input id="${resource}Search" placeholder="Search records"><select id="${resource}Province">${provinceOptions()}</select><select id="${resource}Status"><option value="all">All statuses</option>${['Pending','New','Contacted','Under Review','Mentorship Assigned','Funding Support','Business Established','Marketplace Ready','Approved','In progress','Completed','Rejected','Closed','Cancelled'].map(x=>`<option>${x}</option>`).join('')}</select></div></div><div class="panel table-wrap"><div id="${resource}Table"></div></div>`;const render=async()=>{const d=await api(`/admin/${resource}?q=${encodeURIComponent($('#'+resource+'Search').value)}&status=${encodeURIComponent($('#'+resource+'Status').value)}`);const province=$('#'+resource+'Province')?.value||'all';const items=(d.items||[]).filter(r=>province==='all'||provinceOf(r)===province);$('#'+resource+'Table').innerHTML=items.length?table(cfg.cols,items.map(cfg.row)):empty('No matching records for this province and status.')};$('#'+resource+'Search').oninput=debounce(render,250);$('#'+resource+'Province').onchange=render;$('#'+resource+'Status').onchange=render;await render()}
const table=(cols,rows)=>`<table class="table"><thead><tr>${cols.map(c=>`<th>${c}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
function debounce(fn,ms){let t;return()=>{clearTimeout(t);t=setTimeout(fn,ms)}}
window.openRecord=async(resource,id)=>{const [r,users]=await Promise.all([api(`/admin/${resource}/${id}`),api('/admin/users')]);const excluded=['id','assigned_to_id','internal_notes','created_at','updated_at','assigned_to'];const fields=Object.entries(r).filter(([k])=>!excluded.includes(k));if(!fields.some(([k])=>k==='province'))fields.splice(2,0,['province',provinceOf(r)]);$('#drawerBody').innerHTML=`<span class="kicker">${esc(resource.slice(0,-1))} record</span><h2>${esc(nameOf(r))}</h2><p class="ref">${esc(r.reference)}</p><div class="detail-grid">${fields.map(([k,v])=>`<div class="detail"><span>${esc(k.replaceAll('_',' '))}</span><strong>${esc(v)}</strong></div>`).join('')}</div><form id="recordForm"><div class="form-grid"><label>Status<select id="recordStatus">${['Pending','New','Contacted','Under Review','Mentorship Assigned','Funding Support','Business Established','Marketplace Ready','Approved','In progress','Completed','Rejected','Closed','Cancelled'].map(s=>`<option ${r.status===s?'selected':''}>${s}</option>`).join('')}</select></label><label>Assigned administrator<select id="recordOwner"><option value="">Unassigned</option>${users.filter(u=>u.is_active).map(u=>`<option value="${u.id}" ${r.assigned_to_id===u.id?'selected':''}>${esc(u.full_name)}</option>`).join('')}</select></label>${resource==='orders'?`<label>Quoted amount (R)<input id="quotedAmount" type="number" step="0.01" min="0" value="${r.quoted_amount||''}"></label>`:''}<label class="full">Internal notes<textarea id="internalNotes" rows="5">${esc(r.internal_notes||'')}</textarea></label></div><div class="form-actions"><button type="button" class="btn btn-secondary" onclick="closeDrawer()">Cancel</button><button class="btn btn-primary">Save changes</button></div></form>`;openDrawer();$('#recordForm').onsubmit=async e=>{e.preventDefault();const payload={status:$('#recordStatus').value,assigned_to_id:$('#recordOwner').value?Number($('#recordOwner').value):null,internal_notes:$('#internalNotes').value};if(resource==='orders')payload.quoted_amount=$('#quotedAmount').value?Number($('#quotedAmount').value):null;await api(`/admin/${resource}/${id}`,{method:'PATCH',body:JSON.stringify(payload)});toast('Record updated');closeDrawer();loadResource(resource)}};
async function loadInventory(){const rows=await api('/admin/inventory');$('#inventory').innerHTML=pageHead('Supply control','Inventory management','Track egg availability by farmer, size, packaging and expiry.',`<button class="btn btn-primary" onclick="openInventoryModal()">Add inventory lot</button>`)+`<div class="panel table-wrap">${rows.length?table(['Reference','Farmer','Egg size','Packaging','Available','Price','Status'],rows.map(r=>[esc(r.reference),esc(r.farmer_name),esc(r.egg_size),esc(r.packaging),`${r.trays_available} trays`,r.unit_price?fmtMoney(r.unit_price):'\u2014',badge(r.status)])):empty()}</div>`}
window.openInventoryModal=async()=>{const farmers=(await api('/admin/farmers?status=Approved')).items;openForm('Add inventory lot',`<label>Farmer<select id="iFarmer" required>${farmers.map(x=>`<option value="${x.id}">${esc(x.farm_name)}</option>`).join('')}</select></label><label>Egg size<input id="iSize" required></label><label>Packaging<input id="iPack" required></label><label>Trays available<input id="iTrays" type="number" min="0" required></label><label>Unit price (R)<input id="iPrice" type="number" min="0" step=".01"></label><label>Status<select id="iStatus"><option>Available</option><option>Reserved</option><option>Sold</option><option>Expired</option></select></label>`,async()=>{await api('/admin/inventory',{method:'POST',body:JSON.stringify({farmer_id:+$('#iFarmer').value,egg_size:$('#iSize').value,packaging:$('#iPack').value,trays_available:+$('#iTrays').value,unit_price:$('#iPrice').value?+$('#iPrice').value:null,status:$('#iStatus').value})});loadInventory()})}

async function loadMarketplace(){
  const [overview,inventory,quotes,admins]=await Promise.all([
    api('/admin/marketplace/overview'),
    api('/admin/marketplace/inventory'),
    api('/admin/marketplace/quotes'),
    api('/admin/users')
  ]);
  const view=$('#marketplace');
  view.innerHTML=pageHead(
    'Marketplace operations',
    'Supplier, stock and quotation control',
    'Publish approved supplier inventory, control public stock and convert buyer enquiries into managed commercial quotations.',
    `<button class="btn btn-secondary" onclick="window.open('/marketplace/','_blank')">Open public marketplace</button>
     <button class="btn btn-primary" onclick="openMarketplaceInventoryModal()">Add public inventory</button>`
  )+
  `<div class="metrics marketplace-metrics">
    ${[
      ['\u2659','Approved suppliers',overview.approved_suppliers,'Eligible for public listings'],
      ['\u25A3','Active inventory lots',overview.active_inventory_lots,'Currently marked available'],
      ['\u25CF','Available trays',Number(overview.available_trays).toLocaleString('en-ZA'),'Public stock quantity'],
      ['\u25CE','Marketplace quotes',overview.marketplace_quotes,'Buyer quotation requests'],
      ['R','Quoted value',fmtMoney(overview.quoted_value),'Recorded quotation value']
    ].map(([i,l,v,s])=>`<article class="metric"><span class="metric-icon">${i}</span><span class="label">${l}</span><strong>${v}</strong><small>${s}</small></article>`).join('')}
  </div>
  <div class="marketplace-tabs">
    <button class="active" data-market-tab="inventory">Public inventory</button>
    <button data-market-tab="quotes">Quotation requests <span>${overview.pending_quotes}</span></button>
  </div>
  <section id="marketInventoryPanel" class="marketplace-panel">
    <div class="panel table-wrap">
      ${inventory.length?table(
        ['Reference','Supplier','Location','Product','Available','Price','Status','Updated',''],
        inventory.map(r=>[
          `${esc(r.reference)}<div class="ref">${esc(r.farmer_status)}</div>`,
          esc(r.farmer_name),
          esc(r.location),
          `${esc(r.egg_size)}<div class="ref">${esc(r.packaging)}</div>`,
          `${Number(r.trays_available).toLocaleString('en-ZA')} trays`,
          r.unit_price!==null?fmtMoney(r.unit_price):'Quote only',
          badge(r.status),
          fmtDate(r.updated_at),
          `<div class="row-actions">
            <button class="link-btn" onclick="openMarketplaceInventoryModal(${r.id})">Edit</button>
            ${isCEO()?`<button class="reject-btn" onclick="deleteMarketplaceInventory(${r.id},'${esc(r.reference)}')">Delete</button>`:''}
          </div>`
        ])
      ):empty('No marketplace inventory yet.','Add stock for an approved supplier to publish it on the public marketplace.')}
    </div>
  </section>
  <section id="marketQuotesPanel" class="marketplace-panel hidden">
    <div class="panel table-wrap">
      ${quotes.length?table(
        ['Reference','Buyer','Product','Quantity','Delivery','Required','Status','Quoted',''],
        quotes.map(r=>[
          esc(r.reference),
          `${esc(r.business_name)}<div class="ref">${esc(r.contact_person)}</div>`,
          `${esc(r.egg_size)}<div class="ref">${esc(r.packaging)}</div>`,
          esc(r.quantity),
          esc(r.delivery_area),
          fmtDate(r.required_date),
          badge(r.status),
          r.quoted_amount?fmtMoney(r.quoted_amount):'Not quoted',
          `<button class="link-btn" onclick="openMarketplaceQuote(${r.id})">Manage</button>`
        ])
      ):empty('No marketplace quotations yet.','Buyer quotation requests from the public marketplace will appear here automatically.')}
    </div>
  </section>`;
  $$('#marketplace [data-market-tab]').forEach(btn=>btn.onclick=()=>{
    $$('#marketplace [data-market-tab]').forEach(x=>x.classList.toggle('active',x===btn));
    $('#marketInventoryPanel').classList.toggle('hidden',btn.dataset.marketTab!=='inventory');
    $('#marketQuotesPanel').classList.toggle('hidden',btn.dataset.marketTab!=='quotes');
  });
  window.marketplaceCache={inventory,quotes,admins};
}

window.openMarketplaceInventoryModal=async(id=null)=>{
  const farmers=(await api('/admin/farmers?status=Approved')).items;
  const existing=id?(window.marketplaceCache?.inventory||[]).find(x=>x.id===id):null;
  if(!farmers.length){
    toast('Approve at least one farmer before adding marketplace inventory.',false);
    return;
  }
  openForm(
    existing?'Edit public inventory':'Add public inventory',
    `<label>Approved supplier<select id="miFarmer" required ${existing?'disabled':''}>
      ${farmers.map(x=>`<option value="${x.id}" ${(existing?.farmer_id===x.id)?'selected':''}>${esc(x.farm_name)} \u00B7 ${esc(x.location)}</option>`).join('')}
    </select></label>
    <label>Product / egg size<input id="miSize" required value="${esc(existing?.egg_size||'')}"></label>
    <label>Packaging<input id="miPack" required value="${esc(existing?.packaging||'')}"></label>
    <label>Trays available<input id="miTrays" type="number" min="0" required value="${existing?.trays_available??0}"></label>
    <label>Unit price (R)<input id="miPrice" type="number" min="0" step=".01" value="${existing?.unit_price??''}" placeholder="Leave empty for quote only"></label>
    <label>Available from<input id="miFrom" type="date" value="${existing?.available_from?String(existing.available_from).slice(0,10):new Date().toISOString().slice(0,10)}"></label>
    <label>Expiry date<input id="miExpiry" type="date" value="${existing?.expiry_date?String(existing.expiry_date).slice(0,10):''}"></label>
    <label>Status<select id="miStatus">${['Available','Reserved','Sold','Expired'].map(s=>`<option ${existing?.status===s?'selected':''}>${s}</option>`).join('')}</select></label>
    <label class="full">Internal stock notes<textarea id="miNotes" rows="4">${esc(existing?.notes||'')}</textarea></label>`,
    async()=>{
      const payload={
        farmer_id:+$('#miFarmer').value,
        egg_size:$('#miSize').value.trim(),
        packaging:$('#miPack').value.trim(),
        trays_available:+$('#miTrays').value,
        unit_price:$('#miPrice').value?+$('#miPrice').value:null,
        available_from:$('#miFrom').value,
        expiry_date:$('#miExpiry').value||null,
        status:$('#miStatus').value,
        notes:$('#miNotes').value.trim()||null
      };
      await api(
        existing?`/admin/marketplace/inventory/${existing.id}`:'/admin/marketplace/inventory',
        {method:existing?'PATCH':'POST',body:JSON.stringify(payload)}
      );
      toast(existing?'Inventory updated':'Inventory published');
      closeModal();
      loadMarketplace();
    }
  );
}

window.deleteMarketplaceInventory=async(id,reference)=>{
  if(!requireCEO())return;
  if(!confirm(`Permanently delete inventory ${reference}? This cannot be undone.`))return;
  await api(`/admin/marketplace/inventory/${id}`,{method:'DELETE'});
  toast('Inventory removed');
  loadMarketplace();
}

window.openMarketplaceQuote=async id=>{
  const quote=(window.marketplaceCache?.quotes||[]).find(x=>x.id===id);
  const admins=window.marketplaceCache?.admins||[];
  if(!quote){toast('Quotation request not found.',false);return}
  $('#drawerBody').innerHTML=`<span class="kicker">Marketplace quotation</span>
    <h2>${esc(quote.business_name)}</h2><p class="ref">${esc(quote.reference)}</p>
    <div class="detail-grid">
      ${profileDetail('Contact',esc(quote.contact_person))}
      ${profileDetail('Phone',esc(quote.phone))}
      ${profileDetail('Email',esc(quote.email))}
      ${profileDetail('Product',esc(quote.egg_size))}
      ${profileDetail('Packaging',esc(quote.packaging))}
      ${profileDetail('Quantity',esc(quote.quantity))}
      ${profileDetail('Frequency',esc(quote.frequency))}
      ${profileDetail('Delivery area',esc(quote.delivery_area))}
      ${profileDetail('Required date',fmtDate(quote.required_date))}
      ${profileDetail('Current status',badge(quote.status))}
    </div>
    <form id="marketQuoteForm">
      <div class="form-grid">
        <label>Status<select id="mqStatus">
          ${['Pending','In progress','Approved','Completed','Rejected','Cancelled'].map(s=>`<option ${quote.status===s?'selected':''}>${s}</option>`).join('')}
        </select></label>
        <label>Assigned administrator<select id="mqOwner">
          <option value="">Unassigned</option>
          ${admins.filter(x=>x.is_active).map(x=>`<option value="${x.id}" ${quote.assigned_to_id===x.id?'selected':''}>${esc(x.full_name)}</option>`).join('')}
        </select></label>
        <label>Quoted amount (R)<input id="mqAmount" type="number" min="0" step=".01" value="${quote.quoted_amount||''}"></label>
        <label class="full">Internal commercial notes<textarea id="mqNotes" rows="6">${esc(quote.internal_notes||'')}</textarea></label>
      </div>
      <div class="form-actions"><button type="button" class="btn btn-secondary" onclick="closeDrawer()">Cancel</button><button class="btn btn-primary">Save quotation</button></div>
    </form>`;
  openDrawer();
  $('#marketQuoteForm').onsubmit=async e=>{
    e.preventDefault();
    await api(`/admin/marketplace/quotes/${quote.id}`,{
      method:'PATCH',
      body:JSON.stringify({
        status:$('#mqStatus').value,
        assigned_to_id:$('#mqOwner').value?+$('#mqOwner').value:null,
        quoted_amount:$('#mqAmount').value?+$('#mqAmount').value:null,
        internal_notes:$('#mqNotes').value.trim()||null
      })
    });
    toast('Marketplace quotation updated');
    closeDrawer();
    loadMarketplace();
  };
}

async function loadLogistics(){const [d,v]=await Promise.all([api('/admin/dispatches'),api('/admin/vehicles')]);$('#logistics').innerHTML=pageHead('National fulfilment','Logistics & dispatch','Schedule collections, assign vehicles and monitor delivery status.',`<button class="btn btn-secondary" onclick="openVehicleModal()">Add vehicle</button> <button class="btn btn-primary" onclick="openDispatchModal()">Schedule dispatch</button>`)+`<div class="grid-2"><div class="panel table-wrap">${d.length?table(['Dispatch','Order','Vehicle','Date','Trays','Status'],d.map(x=>[esc(x.reference),esc(x.order_reference),esc(x.vehicle_registration||x.driver_name),fmtDate(x.scheduled_date),x.trays,badge(x.status)])):empty('No dispatches scheduled.')}</div><div class="panel table-wrap">${v.length?table(['Registration','Type','Capacity','Driver','Status'],v.map(x=>[esc(x.registration),esc(x.vehicle_type),`${x.capacity_trays} trays`,esc(x.driver_name),badge(x.status)])):empty('No vehicles registered.')}</div></div>`}
window.openVehicleModal=()=>openForm('Add vehicle',`<label>Registration<input id="vReg" required></label><label>Vehicle type<input id="vType" required></label><label>Capacity (trays)<input id="vCap" type="number" min="0" required></label><label>Driver name<input id="vDriver"></label><label>Driver phone<input id="vPhone"></label><label>Status<select id="vStatus"><option>Available</option><option>In service</option><option>Maintenance</option></select></label>`,async()=>{await api('/admin/vehicles',{method:'POST',body:JSON.stringify({registration:$('#vReg').value,vehicle_type:$('#vType').value,capacity_trays:+$('#vCap').value,driver_name:$('#vDriver').value||null,driver_phone:$('#vPhone').value||null,status:$('#vStatus').value})});loadLogistics()});
window.openDispatchModal=async()=>{const [orders,vehicles]=await Promise.all([api('/admin/orders?status=Approved'),api('/admin/vehicles')]);openForm('Schedule dispatch',`<label>Order<select id="dOrder" required>${orders.items.map(x=>`<option value="${x.id}">${esc(x.reference)} \u00B7 ${esc(x.business_name)}</option>`).join('')}</select></label><label>Vehicle<select id="dVehicle"><option value="">Unassigned</option>${vehicles.map(x=>`<option value="${x.id}">${esc(x.registration)}</option>`).join('')}</select></label><label>Collection location<input id="dFrom" required></label><label>Delivery location<input id="dTo" required></label><label>Scheduled date<input id="dDate" type="datetime-local" required></label><label>Trays<input id="dTrays" type="number" min="0" required></label>`,async()=>{await api('/admin/dispatches',{method:'POST',body:JSON.stringify({order_id:+$('#dOrder').value,vehicle_id:$('#dVehicle').value?+$('#dVehicle').value:null,collection_location:$('#dFrom').value,delivery_location:$('#dTo').value,scheduled_date:new Date($('#dDate').value).toISOString(),trays:+$('#dTrays').value})});loadLogistics()})}
async function loadQuality(){const rows=await api('/admin/quality-cases');$('#quality').innerHTML=pageHead('Product assurance','Quality control','Record inspections, damaged stock, non-conformances and corrective action.',`<button class="btn btn-primary" onclick="openQualityModal()">Open quality case</button>`)+`<div class="panel table-wrap">${rows.length?table(['Reference','Type','Severity','Trays affected','Status','Created'],rows.map(x=>[esc(x.reference),esc(x.case_type),badge(x.severity),x.trays_affected,badge(x.status),fmtDate(x.created_at)])):empty()}</div>`}
window.openQualityModal=()=>openForm('Open quality case',`<label>Case type<input id="qType" placeholder="Damaged stock, shell quality..." required></label><label>Severity<select id="qSeverity"><option>Low</option><option selected>Medium</option><option>High</option><option>Critical</option></select></label><label>Order ID<input id="qOrder" type="number" min="1"></label><label>Farmer ID<input id="qFarmer" type="number" min="1"></label><label>Trays affected<input id="qTrays" type="number" min="0" required></label><label class="full">Findings<textarea id="qFindings"></textarea></label>`,async()=>{await api('/admin/quality-cases',{method:'POST',body:JSON.stringify({case_type:$('#qType').value,severity:$('#qSeverity').value,order_id:$('#qOrder').value?+$('#qOrder').value:null,farmer_id:$('#qFarmer').value?+$('#qFarmer').value:null,trays_affected:+$('#qTrays').value,findings:$('#qFindings').value||null})});loadQuality()})
async function loadFinance(){const [inv,sp,tx,rf]=await Promise.all([api('/admin/invoices'),api('/admin/supplier-payments'),api('/admin/payment-transactions'),api('/admin/refunds')]);const outstanding=inv.reduce((s,x)=>s+Math.max(0,Number(x.total_amount)-Number(x.amount_paid)),0);$('#finance').innerHTML=pageHead('Financial governance','Finance centre','Invoices, supplier settlements, Paystack transactions, balances and refunds.',`<button class="btn btn-secondary" onclick="openSupplierPaymentModal()">Supplier payment</button> <button class="btn btn-primary" onclick="openInvoiceModal()">Create invoice</button>`)+`<div class="metrics"><article class="metric"><span class="label">Outstanding invoices</span><strong>${fmtMoney(outstanding)}</strong><small>${inv.filter(x=>x.status!=='Paid').length} open documents</small></article><article class="metric"><span class="label">Paystack transactions</span><strong>${tx.length}</strong><small>Server-verified records</small></article><article class="metric"><span class="label">Supplier payments</span><strong>${sp.length}</strong><small>Farmer settlements</small></article><article class="metric"><span class="label">Refund cases</span><strong>${rf.length}</strong><small>Controlled workflow</small></article></div><div class="grid-2"><div class="panel table-wrap">${inv.length?table(['Invoice','Customer','Total','Paid','Balance','Status','PDF'],inv.map(x=>[esc(x.reference),esc(x.customer_name),fmtMoney(x.total_amount),fmtMoney(x.amount_paid),fmtMoney(Number(x.total_amount)-Number(x.amount_paid)),badge(x.status),`<button class="link-btn" onclick="downloadFile('/admin/invoices/${x.id}/pdf','${esc(x.reference)}.pdf')">Download</button>`])):empty('No invoices created.')}</div><div class="panel table-wrap">${sp.length?table(['Reference','Farmer','Amount','Method','Status'],sp.map(x=>[esc(x.reference),esc(x.farmer_name),fmtMoney(x.amount),esc(x.method),badge(x.status)])):empty('No supplier payments.')}</div></div>`}
window.openInvoiceModal=()=>openForm('Create invoice',`<label>Related type<select id="fType"><option>order</option><option>membership</option></select></label><label>Record ID<input id="fEntity" type="number" min="1" required></label><label>Customer name<input id="fName" required></label><label>Customer email<input id="fEmail" type="email"></label><label>Subtotal (R)<input id="fSub" type="number" min="0" step=".01" required></label><label>Tax (R)<input id="fTax" type="number" min="0" step=".01" value="0"></label><label>Due date<input id="fDue" type="date" required></label><label class="full">Description<textarea id="fDesc" required></textarea></label>`,async()=>{await api('/admin/invoices',{method:'POST',body:JSON.stringify({entity_type:$('#fType').value,entity_id:+$('#fEntity').value,customer_name:$('#fName').value,customer_email:$('#fEmail').value||null,subtotal:+$('#fSub').value,tax_amount:+$('#fTax').value,due_date:$('#fDue').value,description:$('#fDesc').value})});loadFinance()});
window.openSupplierPaymentModal=async()=>{const farmers=(await api('/admin/farmers?status=Approved')).items;openForm('Record supplier payment',`<label>Farmer<select id="sFarmer">${farmers.map(x=>`<option value="${x.id}">${esc(x.farm_name)}</option>`).join('')}</select></label><label>Order ID<input id="sOrder" type="number" min="1"></label><label>Amount (R)<input id="sAmount" type="number" min=".01" step=".01" required></label><label>Method<select id="sMethod"><option>EFT</option><option>PayShap</option><option>Cash deposit</option></select></label><label>Bank reference<input id="sRef"></label><label>Status<select id="sStatus"><option>Pending</option><option>Approved</option><option>Paid</option><option>Failed</option></select></label>`,async()=>{await api('/admin/supplier-payments',{method:'POST',body:JSON.stringify({farmer_id:+$('#sFarmer').value,order_id:$('#sOrder').value?+$('#sOrder').value:null,amount:+$('#sAmount').value,method:$('#sMethod').value,bank_reference:$('#sRef').value||null,status:$('#sStatus').value})});loadFinance()})}
async function loadPayments(){const rows=await api('/admin/payments');$('#payments').innerHTML=pageHead('Finance control','Payment records','Manual Capitec EFT, PayShap, deposit and card records.',`<button class="btn btn-primary" onclick="openPaymentModal()">Add payment record</button>`)+`<div class="panel table-wrap">${rows.length?table(['Reference','Payer','Amount','Method','Status','Date'],rows.map(r=>[esc(r.reference),esc(r.payer_name),fmtMoney(r.amount),esc(r.method),badge(r.status),fmtDate(r.created_at)])):empty()}</div>`}
window.openPaymentModal=()=>openForm('Add payment record',`<label>Related to<select id="pType"><option value="order">Order</option><option value="membership">Membership</option></select></label><label>Record ID<input id="pEntity" type="number" min="1" required></label><label>Payer name<input id="pName" required></label><label>Amount (R)<input id="pAmount" type="number" step=".01" min=".01" required></label><label>Method<select id="pMethod"><option>EFT / bank transfer</option><option>PayShap</option><option>Card</option><option>Cash deposit</option></select></label><label>Status<select id="pStatus"><option>Pending</option><option>Invoiced</option><option>Part paid</option><option>Paid</option><option>Failed</option><option>Refunded</option></select></label>`,async()=>{await api('/admin/payments',{method:'POST',body:JSON.stringify({entity_type:$('#pType').value,entity_id:+$('#pEntity').value,payer_name:$('#pName').value,amount:+$('#pAmount').value,method:$('#pMethod').value,status:$('#pStatus').value})});loadPayments()})
async function loadNotifications(){const rows=await api('/admin/notifications');$('#notifications').innerHTML=pageHead('Customer communication','Communications','Send email notifications and maintain a permanent delivery queue.',`<button class="btn btn-primary" onclick="openNotificationModal()">Create notification</button>`)+`<div class="panel table-wrap">${rows.length?table(['Channel','Recipient','Subject','Status','Sent'],rows.map(x=>[esc(x.channel),esc(x.recipient),esc(x.subject),badge(x.status),fmtDate(x.sent_at||x.created_at)])):empty()}</div>`}
window.openNotificationModal=()=>openForm('Create notification',`<label>Channel<select id="nChannel"><option>Email</option><option>SMS</option><option>WhatsApp</option></select></label><label>Recipient<input id="nRecipient" required></label><label class="full">Subject<input id="nSubject"></label><label class="full">Message<textarea id="nMessage" rows="6" required></textarea></label>`,async()=>{await api('/admin/notifications',{method:'POST',body:JSON.stringify({channel:$('#nChannel').value,recipient:$('#nRecipient').value,subject:$('#nSubject').value||null,message:$('#nMessage').value})});loadNotifications()})
async function loadDocuments(){const rows=await api('/admin/documents');$('#documents').innerHTML=pageHead('Secure records','Document centre','Store supporting documents in PostgreSQL with authenticated download access.',`<button class="btn btn-primary" onclick="openDocumentModal()">Upload document</button>`)+`<div class="panel table-wrap">${rows.length?table(['Reference','Type','Entity','Filename','Size','Uploaded',''],rows.map(x=>[esc(x.reference),esc(x.document_type),`${esc(x.entity_type)} #${x.entity_id}`,esc(x.filename),`${Math.ceil(x.file_size/1024)} KB`,fmtDate(x.created_at),`<button class="link-btn" onclick="downloadFile('/admin/documents/${x.id}/download','${esc(x.filename)}')">Download</button>`])):empty()}</div>`}
window.openDocumentModal=()=>{openModal();$('#modalBody').innerHTML=`<span class="kicker">Secure storage</span><h2>Upload document</h2><form id="docForm" class="form-grid"><label>Entity type<select id="docType"><option>farmer</option><option>buyer</option><option>order</option><option>payment</option></select></label><label>Entity ID<input id="docEntity" type="number" min="1" required></label><label class="full">Document type<input id="docLabel" placeholder="Proof of payment, CIPC, certificate..." required></label><label class="full">File<input id="docFile" type="file" required></label><div class="form-actions full"><button class="btn btn-primary">Upload securely</button></div></form>`;$('#docForm').onsubmit=async e=>{e.preventDefault();const fd=new FormData();fd.append('entity_type',$('#docType').value);fd.append('entity_id',$('#docEntity').value);fd.append('document_type',$('#docLabel').value);fd.append('file',$('#docFile').files[0]);const r=await fetch(API+'/admin/documents',{method:'POST',headers:{Authorization:`Bearer ${token}`},body:fd});if(!r.ok)throw new Error((await r.json()).detail||'Upload failed');toast('Document uploaded');closeModal();loadDocuments()}}
async function loadUsers(){
  if(!requireCEO()){
    $('#users').innerHTML=pageHead('Access governance','Administrator management','This section is restricted to the protected CEO account.','')+
      `<div class="panel"><div class="empty"><strong>CEO authorisation required</strong><p>Sign in with the CEO account to manage administrators.</p></div></div>`;
    return;
  }

  const users=await api('/admin/users');
  $('#users').innerHTML=
    pageHead('Access governance','Administrator management','Create administrators, assign roles and preserve accountable access from one protected CEO workspace.',
      `<button class="btn btn-primary admin-add-btn" id="addAdministratorBtn" type="button">+ Add administrator</button>`)+
    `<div class="admin-summary">
      <article><span>Total administrators</span><strong>${users.length}</strong></article>
      <article><span>Active accounts</span><strong>${users.filter(u=>u.is_active).length}</strong></article>
      <article><span>Suspended accounts</span><strong>${users.filter(u=>!u.is_active).length}</strong></article>
      <article><span>Protected owner</span><strong>${users.filter(u=>String(u.role).toUpperCase()==='CEO').length} CEO</strong></article>
    </div>
    <div class="admin-controls toolbar">
      <input id="administratorSearch" placeholder="Search name, email, title or role">
      <select id="administratorRole">
        <option value="all">All roles</option>
        <option value="CEO">CEO</option><option value="FINANCE">Finance</option>
        <option value="OPERATIONS">Operations</option><option value="LOGISTICS">Logistics</option>
        <option value="QUALITY">Quality control</option><option value="ADMIN">Administrator</option>
      </select>
      <select id="administratorStatus">
        <option value="all">All statuses</option><option value="active">Active</option><option value="suspended">Suspended</option>
      </select>
    </div>
    <div id="administratorTable" class="panel table-wrap"></div>`;

  const render=()=>{
    const q=$('#administratorSearch').value.trim().toLowerCase();
    const role=$('#administratorRole').value;
    const status=$('#administratorStatus').value;
    const filtered=users.filter(u=>{
      const hay=`${u.full_name} ${u.email} ${u.job_title} ${u.role}`.toLowerCase();
      return (!q||hay.includes(q)) &&
        (role==='all'||String(u.role).toUpperCase()===role) &&
        (status==='all'||(status==='active'&&u.is_active)||(status==='suspended'&&!u.is_active));
    });

    $('#administratorTable').innerHTML=filtered.length?table(
      ['Administrator','Department & role','Status','Created by','Last activity','Last login','Actions'],
      filtered.map(u=>[
        `<div class="admin-identity"><span class="admin-avatar">${esc((u.full_name||'A').split(' ').map(x=>x[0]).slice(0,2).join(''))}</span><div><strong>${esc(u.full_name)}</strong><div class="ref">${esc(u.email)}</div></div></div>`,
        `<strong>${esc(u.job_title||'Administrator')}</strong><div>${roleBadge(u.role)}</div>`,
        badge(u.is_active?'Approved':'Rejected'),
        esc(u.created_by||'Not recorded'),
        `<strong>${esc(u.last_activity||'No activity')}</strong>${u.last_activity_at?`<div class="ref">${new Date(u.last_activity_at).toLocaleDateString('en-ZA')}</div>`:''}`,
        fmtAdminDate(u.last_login_at),
        `<div class="admin-action-cell">${String(u.role||'').toUpperCase()==='CEO'?'<span class="protected-owner">Protected CEO</span>':''}<button class="icon-action" onclick="openAdminActions(${u.id},${String(u.role||'').toUpperCase()==='CEO'})" aria-label="Open administrator actions">\u22EE</button></div>`
      ])
    ):empty('No administrators match the selected search and filters.');
  };

  $('#administratorSearch').oninput=debounce(render,180);
  $('#administratorRole').onchange=render;
  $('#administratorStatus').onchange=render;
  $('#addAdministratorBtn').onclick=openUserModal;
  render();
}

window.openAdminActions=async(id,isProtected=false)=>{
  if(!requireCEO())return;
  openDrawer('<div class="drawer-loading"><span></span><strong>Loading administrator actions\u2026</strong></div>');
  try{
    const u=await api(`/admin/users/${id}`);
    window.selectedAdministrator=u;
    const actions=[
      `<button onclick="viewAdministrator(${id})">View profile</button>`,
      `<button onclick="editAdministrator(${id})">Edit details and role</button>`,
      `<button onclick="resetAdministratorPassword(${id})">Reset temporary password</button>`,
      `<button onclick="viewAdministratorAudit(${id})">View audit history</button>`
    ];
    if(!isProtected){
      actions.push(`<button onclick="toggleUser(${id},${!u.is_active})">${u.is_active?'Suspend account':'Reactivate account'}</button>`);
      actions.push(`<button class="danger" onclick="removeUser(${id})">Delete account</button>`);
    }
    openDrawer(`<span class="kicker">Access governance</span><h2>${esc(u.full_name)}</h2><p class="muted">${esc(u.job_title)} \u00B7 ${esc(u.role)}</p><div class="admin-action-menu">${actions.join('')}</div>`);
  }catch(e){closeDrawer();toast(e.message||'Unable to load administrator actions.',false)}
};

window.viewAdministrator=async id=>{
  openDrawer('<div class="drawer-loading"><span></span><strong>Loading administrator profile\u2026</strong></div>');
  try{
    let u=window.selectedAdministrator;
    if(!u||Number(u.id)!==Number(id))u=await api(`/admin/users/${id}`);
    window.selectedAdministrator=u;

    const initials=esc((u.full_name||'A').split(' ').map(x=>x[0]).slice(0,2).join(''));
    const protectedCEO=String(u.role||'').toUpperCase()==='CEO';

    openDrawer(`
      <div class="profile-drawer-head">
        <span class="profile-avatar">${initials}</span>
        <div>
          <span class="kicker">Administrator profile</span>
          <h2>${esc(u.full_name)}</h2>
          <p class="muted">${esc(u.job_title||'Administrator')} \u00B7 ${roleBadge(u.role)}</p>
        </div>
      </div>

      <div class="profile-status-row">
        ${badge(u.is_active?'Approved':'Rejected')}
        ${protectedCEO?'<span class="protected-owner">Protected CEO account</span>':''}
      </div>

      <section class="profile-section">
        <h3>Account information</h3>
        <div class="detail-grid">
          ${profileDetail('Email address',u.email)}
          ${profileDetail('Department role',u.role)}
          ${profileDetail('Account status',u.is_active?'Active':'Suspended')}
          ${profileDetail('Password status',u.must_change_password?'Temporary password active':'Password changed')}
          ${profileDetail('Created',u.created_at?new Date(u.created_at).toLocaleString('en-ZA'):'Not recorded')}
          ${profileDetail('Last login',u.last_login_at?new Date(u.last_login_at).toLocaleString('en-ZA'):'Never')}
        </div>
      </section>

      <section class="profile-section">
        <h3>Governance</h3>
        <div class="profile-governance">
          <div><span>Created by</span><strong>${esc(u.created_by||'System')}</strong></div>
          <div><span>Last activity</span><strong>${esc(u.last_activity||'No activity')}</strong></div>
          <div><span>Access level</span><strong>${protectedCEO?'Full executive control':esc(u.role||'Administrator')}</strong></div>
        </div>
      </section>

      <div class="drawer-actions">
        <button class="btn btn-primary" onclick="editAdministrator(${id})">Edit profile</button>
        <button class="btn btn-secondary" onclick="resetAdministratorPassword(${id})">Reset password</button>
        <button class="btn btn-secondary" onclick="viewAdministratorAudit(${id})">View audit history</button>
      </div>
    `);
  }catch(e){
    console.error('Administrator profile error:',e);
    openDrawer(`<div class="drawer-error"><strong>Unable to load profile</strong><p>${esc(e?.message||'The administrator profile could not be loaded.')}</p><button class="btn btn-secondary" onclick="closeDrawer()">Close</button></div>`);
  }
};

window.editAdministrator=async id=>{
  const u=await api(`/admin/users/${id}`);
  const protectedCEO=String(u.role||'').toUpperCase()==='CEO';
  openForm('Edit administrator',`
    <label>Full name<input id="eName" value="${esc(u.full_name)}" required></label>
    <label>Email address<input id="eEmail" type="email" value="${esc(u.email)}" required></label>
    <label>Job title<input id="eTitle" value="${esc(u.job_title)}" required></label>
    <label>Department role<select id="eRole" ${protectedCEO?'disabled':''}>
      ${['ADMIN','FINANCE','OPERATIONS','LOGISTICS','QUALITY'].map(r=>`<option value="${r}" ${u.role===r?'selected':''}>${r}</option>`).join('')}
      ${protectedCEO?'<option value="CEO" selected>CEO</option>':''}
    </select></label>`,
    async()=>{
      await api(`/admin/users/${id}`,{method:'PATCH',body:JSON.stringify({
        full_name:$('#eName').value.trim(),email:$('#eEmail').value.trim().toLowerCase(),
        job_title:$('#eTitle').value.trim(),role:protectedCEO?'CEO':$('#eRole').value
      })});
      toast('Administrator details updated');await loadUsers();
    });
};

window.resetAdministratorPassword=id=>openForm('Reset administrator password',`
  <label class="full">New temporary password<input id="rPass" type="password" minlength="10" required autocomplete="new-password" placeholder="Minimum 10 characters"></label>
  <div class="full admin-security-note">The administrator must change this temporary password after the next successful login.</div>`,
  async()=>{await api(`/admin/users/${id}/reset-password`,{method:'POST',body:JSON.stringify({temporary_password:$('#rPass').value})});toast('Temporary password created');await loadUsers();});

window.viewAdministratorAudit=async id=>{
  openDrawer('<div class="drawer-loading"><span></span><strong>Loading audit history\u2026</strong></div>');
  try{
    const rows=await api(`/admin/users/${id}/audit`);
    const content=rows.length
      ? `<div class="audit-history-list">${rows.map(r=>`
          <article class="audit-history-item">
            <div class="audit-history-top">
              <strong>${esc(r.action||'Activity')}</strong>
              <time>${r.created_at?new Date(r.created_at).toLocaleString('en-ZA'):'\u2014'}</time>
            </div>
            <div class="audit-history-meta">
              <span><b>Actor</b>${esc(r.actor_name||'System')}</span>
              <span><b>Entity</b>${esc(r.entity_type||'\u2014')}${r.entity_id?' #'+r.entity_id:''}</span>
              <span><b>IP address</b>${esc(r.ip_address||'\u2014')}</span>
            </div>
          </article>`).join('')}</div>`
      : `<div class="empty"><strong>No audit history</strong><p>No administrator-specific activity has been recorded yet.</p></div>`;

    openDrawer(`
      <div class="audit-drawer-head">
        <div>
          <span class="kicker">Security history</span>
          <h2>Administrator audit history</h2>
          <p class="muted">Chronological account activity and governance events.</p>
        </div>
        <span class="formal-badge">${rows.length} record${rows.length===1?'':'s'}</span>
      </div>
      <div class="audit-history-toolbar">
        <input id="adminAuditSearch" placeholder="Search activity, actor or entity">
      </div>
      <div id="adminAuditResults">${content}</div>
    `);

    const render=()=>{
      const q=$('#adminAuditSearch').value.trim().toLowerCase();
      const filtered=rows.filter(r=>`${r.action||''} ${r.actor_name||''} ${r.entity_type||''} ${r.entity_id||''} ${r.ip_address||''}`.toLowerCase().includes(q));
      $('#adminAuditResults').innerHTML=filtered.length
        ? `<div class="audit-history-list">${filtered.map(r=>`
            <article class="audit-history-item">
              <div class="audit-history-top">
                <strong>${esc(r.action||'Activity')}</strong>
                <time>${r.created_at?new Date(r.created_at).toLocaleString('en-ZA'):'\u2014'}</time>
              </div>
              <div class="audit-history-meta">
                <span><b>Actor</b>${esc(r.actor_name||'System')}</span>
                <span><b>Entity</b>${esc(r.entity_type||'\u2014')}${r.entity_id?' #'+r.entity_id:''}</span>
                <span><b>IP address</b>${esc(r.ip_address||'\u2014')}</span>
              </div>
            </article>`).join('')}</div>`
        : `<div class="empty"><strong>No matching activity</strong><p>Try another search term.</p></div>`;
    };
    $('#adminAuditSearch').oninput=debounce(render,160);
  }catch(e){
    console.error('Administrator audit history error:',e);
    openDrawer(`<div class="drawer-error"><strong>Unable to load audit history</strong><p>${esc(e?.message||'The administrator audit history could not be loaded.')}</p><button class="btn btn-secondary" onclick="closeDrawer()">Close</button></div>`);
  }
};

window.openUserModal=()=>{
  if(!requireCEO())return;
  openForm(
    'Add administrator',
    `<label>Full name<input id="uName" required autocomplete="name" placeholder="Administrator full name"></label>
     <label>Email address<input id="uEmail" type="email" required autocomplete="email" placeholder="name@farmlink.co.za"></label>
     <label>Job title<input id="uTitle" required placeholder="Finance Administrator"></label>
     <label>Department role
       <select id="uRole" required>
         <option value="ADMIN">General Administration</option>
         <option value="FINANCE">Finance</option>
         <option value="OPERATIONS">Operations</option>
         <option value="LOGISTICS">Logistics</option>
         <option value="QUALITY">Quality Control</option>
       </select>
     </label>
     <label class="full">Temporary password<input id="uPass" type="password" minlength="10" required autocomplete="new-password" placeholder="Minimum 10 characters"></label>
     <div class="full admin-security-note">The administrator will be required to change this temporary password after first login.</div>`,
    async()=>{
      const payload={
        full_name:$('#uName').value.trim(),
        email:$('#uEmail').value.trim().toLowerCase(),
        job_title:$('#uTitle').value.trim(),
        role:$('#uRole').value,
        temporary_password:$('#uPass').value
      };
      const created=await api('/admin/users',{method:'POST',body:JSON.stringify(payload)});
      toast(`${created.full_name} added successfully`);
      await loadUsers();
    }
  );
};

window.toggleUser=async(id,active)=>{
  if(!requireCEO())return;
  const action=active?'activate':'suspend';
  if(!confirm(`Are you sure you want to ${action} this administrator?`))return;
  try{
    await api(`/admin/users/${id}/status?active=${active}`,{method:'PATCH'});
    toast(`Administrator ${active?'activated':'suspended'}`);
    await loadUsers();
  }catch(err){toast(err.message,false)}
};

window.removeUser=async id=>{
  if(!requireCEO())return;
  if(!confirm('Delete this administrator permanently? Accounts with operational or audit history must be suspended instead.'))return;
  try{
    await api(`/admin/users/${id}`,{method:'DELETE'});
    toast('Administrator removed');
    await loadUsers();
  }catch(err){toast(err.message,false)}
};
async function loadAudit(){const rows=await api('/admin/audit?limit=300');$('#audit').innerHTML=pageHead('Governance','Audit trail','Chronological record of access, approvals and operational decisions.','')+`<div class="panel table-wrap">${rows.length?table(['Date','Actor','Action','Entity'],rows.map(r=>[new Date(r.created_at).toLocaleString('en-ZA'),esc(r.actor_name),esc(r.action),`${esc(r.entity_type)}${r.entity_id?' #'+r.entity_id:''}`])):empty()}</div>`}
window.downloadFile=async(path,name)=>{try{const r=await fetch(API+path,{headers:{Authorization:`Bearer ${token}`}});if(!r.ok)throw new Error('Download failed');const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name||'download';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch(e){toast(e.message,false)}};
function pageHead(k,t,d,a=''){return `<div class="page-head"><div><span class="kicker">${k}</span><h2>${t}</h2><p class="muted">${d}</p></div><div>${a}</div></div>`}
function openForm(title,fields,submit){openModal();$('#modalBody').innerHTML=`<span class="kicker">FarmLink control</span><h2>${title}</h2><form id="dynamicForm" class="form-grid">${fields}<div class="form-actions full"><button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary">Save record</button></div></form>`;$('#dynamicForm').onsubmit=async e=>{e.preventDefault();try{await submit();toast('Record saved');closeModal()}catch(err){toast(err.message,false)}}}
function openPasswordModal(){openModal();$('#modalBody').innerHTML=`<span class="kicker">Security required</span><h2>Change temporary password</h2><p class="muted">Your administrator account must use a private password before continuing.</p><form id="passwordForm" class="form-grid"><label class="full">Current password<input id="oldPass" type="password" required></label><label class="full">New password<input id="newPass" type="password" minlength="10" required></label><div class="form-actions full"><button class="btn btn-primary">Update password</button></div></form>`;$('#passwordForm').onsubmit=async e=>{e.preventDefault();await api('/auth/change-password',{method:'POST',body:JSON.stringify({current_password:$('#oldPass').value,new_password:$('#newPass').value})});currentUser.must_change_password=false;toast('Password updated');closeModal()}}
function openDrawer(content=null){
  if(content!==null&&content!==undefined)$('#drawerBody').innerHTML=content;
  $('#drawer').classList.remove('hidden');
  $('#drawerBackdrop').classList.remove('hidden');
}window.closeDrawer=()=>{
  $('#drawer').classList.add('hidden');
  $('#drawerBackdrop').classList.add('hidden');
  setTimeout(()=>{$('#drawerBody').innerHTML='';window.selectedAdministrator=null},180);
};$('#closeDrawer').onclick=closeDrawer;$('#drawerBackdrop').onclick=closeDrawer;
function openModal(){$('#modal').classList.remove('hidden');$('#modalBackdrop').classList.remove('hidden')}window.closeModal=()=>{$('#modal').classList.add('hidden');$('#modalBackdrop').classList.add('hidden')};$('#closeModal').onclick=closeModal;$('#modalBackdrop').onclick=closeModal;

// v3.0 interface controls
const accountToggle=$('#accountToggle'),accountDropdown=$('#accountDropdown');
accountToggle.onclick=e=>{e.stopPropagation();const open=accountDropdown.classList.toggle('hidden')===false;accountToggle.setAttribute('aria-expanded',String(open))};
document.addEventListener('click',()=>accountDropdown.classList.add('hidden'));
$('#accountLogout').onclick=logout;
$('#profileAction').onclick=()=>{accountDropdown.classList.add('hidden');openPasswordModal()};
$('#mobileNav').onclick=()=>{$('.sidebar').classList.add('open');$('#mobileBackdrop').classList.remove('hidden')};
$('#mobileBackdrop').onclick=()=>{$('.sidebar').classList.remove('open');$('#mobileBackdrop').classList.add('hidden')};
$$('#nav button').forEach(b=>b.addEventListener('click',()=>{$('.sidebar').classList.remove('open');$('#mobileBackdrop').classList.add('hidden')}));
document.addEventListener('keydown',e=>{if(e.key==='Escape'){closeDrawer();closeModal();accountDropdown.classList.add('hidden');$('.sidebar').classList.remove('open');$('#mobileBackdrop').classList.add('hidden')}});

// V4 boot moved to end of file


/* FarmLink Admin V4 \u2014 executive productivity and intelligence */
const ICONS={
 dashboard:'<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>',
 farmers:'<svg viewBox="0 0 24 24"><path d="M12 21V10"/><path d="M7 15c-3 0-4-2-4-5 3 0 5 1 6 4"/><path d="M17 12c3 0 4-2 4-5-3 0-5 1-6 4"/><path d="M8 21h8"/></svg>',
 buyers:'<svg viewBox="0 0 24 24"><path d="M4 10h16"/><path d="M5 10V5h14v5"/><path d="M6 10v9h12v-9"/><path d="M9 14h6"/></svg>',
 orders:'<svg viewBox="0 0 24 24"><path d="M6 3h12v18H6z"/><path d="M9 7h6M9 11h6M9 15h4"/></svg>',
 memberships:'<svg viewBox="0 0 24 24"><path d="M12 3l3 6 6 .9-4.5 4.4 1.1 6.2L12 17.6 6.4 20.5l1.1-6.2L3 9.9 9 9z"/></svg>',
 inventory:'<svg viewBox="0 0 24 24"><path d="M4 7l8-4 8 4-8 4z"/><path d="M4 7v10l8 4 8-4V7"/><path d="M12 11v10"/></svg>',
 logistics:'<svg viewBox="0 0 24 24"><path d="M3 6h11v10H3z"/><path d="M14 10h4l3 3v3h-7z"/><circle cx="7" cy="18" r="2"/><circle cx="18" cy="18" r="2"/></svg>',
 quality:'<svg viewBox="0 0 24 24"><path d="M12 3l8 4v5c0 5-3.4 8.2-8 9-4.6-.8-8-4-8-9V7z"/><path d="M8.5 12l2.2 2.2L16 9"/></svg>',
 finance:'<svg viewBox="0 0 24 24"><path d="M4 7h16v12H4z"/><path d="M4 10h16"/><path d="M8 15h3"/></svg>',
 payments:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.8-.7-1.8-1-3-1-1.7 0-3 .8-3 2s1 1.8 3 2 3 1 3 2.2-1.3 2.1-3 2.1c-1.3 0-2.4-.4-3.2-1.2M12 6.5v11"/></svg>',
 notifications:'<svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 00-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></svg>',
 documents:'<svg viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></svg>',
 users:'<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="4"/><path d="M2 21c.5-4 3-6 7-6s6.5 2 7 6"/><path d="M18 8v6M15 11h6"/></svg>',
 audit:'<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 109-9 9 9 0 00-6.4 2.6L3 8"/><path d="M3 3v5h5M12 7v5l3 2"/></svg>'
};
function installIcons(){
  $$('#nav button').forEach(button=>{const key=button.dataset.view;const slot=button.querySelector('span');if(slot){slot.className='nav-icon';slot.innerHTML=ICONS[key]||'';}});
}

const originalShowView=showView;
showView=async function(name){
  const target=$('#'+name);
  if(target && name!=='dashboard') target.innerHTML=`<div class="skeleton-page"><div class="skeleton skeleton-banner"></div><div class="skeleton skeleton-panel"></div></div>`;
  await originalShowView(name);
  requestAnimationFrame(()=>enhanceTables(target));
};

let revenueChart=null;
loadDashboard=async function(){
  const dashboard=$('#dashboard');
  dashboard.innerHTML=`<div class="skeleton-page"><div class="skeleton skeleton-banner"></div><div class="skeleton-cards">${'<div class="skeleton skeleton-card"></div>'.repeat(5)}</div><div class="skeleton skeleton-panel"></div></div>`;
  const [d,a]=await Promise.all([api('/admin/dashboard'),api('/admin/analytics')]);
  const c=d.counts||{};
  const pendingFarmers=c.farmers?.pending||0,pendingBuyers=c.buyers?.pending||0,openOrders=c.open_orders||0;
  dashboard.innerHTML=`
  <div class="command-banner"><div><span class="kicker light">Operations command</span><h2>National distribution oversight from one accountable system.</h2><p>Monitor registrations, revenue, supply, fulfilment, quality and team activity in real time.</p></div><div class="command-date"><strong>${new Intl.DateTimeFormat('en-ZA',{dateStyle:'full'}).format(new Date())}</strong><span>Gauteng headquarters \u00B7 Nationwide coordination</span></div></div>
  <div class="quick-actions">
    <button class="quick-action" data-jump="farmers"><b>+</b>Review farmers</button><button class="quick-action" data-jump="buyers"><b>+</b>Review buyers</button><button class="quick-action" data-jump="orders"><b>+</b>Manage orders</button><button class="quick-action" data-jump="finance"><b>R</b>Create invoice</button><button class="quick-action" data-jump="users"><b>+</b>Add administrator</button>
  </div>
  <div class="metrics">
    ${metricCard('Today revenue',fmtMoney(a.today_revenue),'Verified payments','R','emerald')}
    ${metricCard('Month revenue',fmtMoney(a.month_revenue),'Current calendar month','\u2197','forest')}
    ${metricCard('Eggs traded',Number(a.total_trays||0).toLocaleString('en-ZA')+' trays','Recorded order volume','\u25C9','gold')}
    ${metricCard('Active farmers',a.active_farmers||0,'Approved suppliers','\u2659','blue')}
    ${metricCard('Delivery performance',(a.delivery_performance||0)+'%','Completed dispatches','\u21C4','teal')}
  </div>
  <div class="metrics secondary-metrics">
    ${metricCard('Pending farmers',pendingFarmers,'Awaiting approval','!')}
    ${metricCard('Pending buyers',pendingBuyers,'Awaiting approval','!')}
    ${metricCard('Open orders',openOrders,'Current pipeline','\u25CE')}
    ${metricCard('Processed records',c.completed||0,'Completed workflow','\u2713')}
    ${metricCard('Membership activity',c.memberships?.pending||0,'Pending applications','\u25C7')}
  </div>
  <div class="grid-2"><article class="panel"><div class="panel-head"><div><span class="kicker">Commercial performance</span><h3>Revenue trend</h3></div><button class="link-btn" onclick="exportChart()">Export PNG</button></div><div class="chart-wrap"><canvas id="revenueChart"></canvas></div></article><article class="panel"><div class="panel-head"><div><span class="kicker">Buyer activity</span><h3>Top customers</h3></div></div><div class="rank-list">${a.top_buyers?.length?a.top_buyers.map((x,i)=>`<div class="rank-item"><span class="rank-num">${i+1}</span><strong>${esc(x.name)}</strong><span>${x.orders} orders</span></div>`).join(''):smartEmpty('No customers yet','Approved buyers and completed orders will appear here.','buyers','Review buyers')}</div></article></div>
  <div class="grid-2" style="margin-top:18px"><article class="panel"><div class="panel-head"><div><span class="kicker">Order pipeline</span><h3>Latest submissions</h3></div></div>${d.latest?.length?d.latest.map(x=>`<div class="list-item"><div><strong>${esc(nameOf(x))}</strong><div class="ref">${esc(x.reference)}</div></div><span>${esc(labelOf(x.type))}</span>${badge(x.status)}<button class="link-btn" onclick="openRecord('${plural(x.type)}',${x.id})">Review</button></div>`).join(''):smartEmpty('No submissions yet','New farmer, buyer and order registrations will appear in this queue.','farmers','Open registrations')}</article><article class="panel"><div class="panel-head"><div><span class="kicker">Supplier strength</span><h3>Top capacity</h3></div></div><div class="rank-list">${a.top_suppliers?.length?a.top_suppliers.map((x,i)=>`<div class="rank-item"><span class="rank-num">${i+1}</span><strong>${esc(x.name)}</strong><span>${Number(x.capacity).toLocaleString()} trays/wk</span></div>`).join(''):smartEmpty('No supplier rankings yet','Approve farmers to begin tracking production capacity.','farmers','Review farmers')}</div></article></div>`;
  try{
    const [allFarmers,allBuyers]=await Promise.all([
      api('/admin/farmers?status=all').catch(()=>({items:[]})),
      api('/admin/buyers?status=all').catch(()=>({items:[]}))
    ]);
    const provinceStats=SA_PROVINCES.map(province=>({
      province,
      farmers:(allFarmers.items||[]).filter(x=>provinceOf(x)===province).length,
      buyers:(allBuyers.items||[]).filter(x=>provinceOf(x)===province).length
    }));
    $('#dashboard').insertAdjacentHTML('beforeend',provinceCoverage(provinceStats));
  }catch{}
  $$('.quick-action').forEach(b=>b.onclick=()=>{const view=b.dataset.jump;showView(view);if(view==='finance')setTimeout(()=>window.openInvoiceModal?.(),350);if(view==='users'&&isCEO())setTimeout(()=>window.openUserModal?.(),350)});
  drawRevenueChart(a.revenue_series||[]);
};
function metricCard(label,value,sub,icon,accent='green'){return `<article class="metric metric-${accent}"><span class="metric-icon">${icon}</span><span class="label">${label}</span><strong>${value}</strong><small>${sub}</small><span class="metric-trend">\u25CF Live data</span></article>`}
function provinceCoverage(rows){
  return `<article class="panel province-panel"><div class="panel-head"><div><span class="kicker">National footprint</span><h3>Provincial coverage</h3></div><span class="formal-badge">South Africa \u00B7 9 Provinces</span></div><div class="province-grid">${rows.map(x=>`<div class="province-card"><strong>${esc(x.province)}</strong><span>${x.farmers} farmers</span><span>${x.buyers} buyers</span></div>`).join('')}</div></article>`;
}
function smartEmpty(title,text,view,action){return `<div class="empty-action"><div class="empty-icon">\u00EF\u00BC\u2039</div><h4>${title}</h4><p>${text}</p><button class="btn btn-secondary" onclick="showView('${view}')">${action}</button></div>`}
function drawRevenueChart(series){
  const canvas=$('#revenueChart');if(!canvas)return;
  if(revenueChart)revenueChart.destroy();
  if(!window.Chart){canvas.replaceWith(Object.assign(document.createElement('div'),{className:'empty',textContent:'Chart library unavailable.'}));return}
  const hasData=series.some(x=>Number(x.value||0)!==0);
  if(!hasData){canvas.parentElement.innerHTML='<div class="chart-empty"><span class="chart-empty-icon">\u2197</span><strong>No revenue data yet</strong><p>Verified payments will appear here automatically.</p></div>';return;}
  revenueChart=new Chart(canvas,{type:'line',data:{labels:series.map(x=>x.label),datasets:[{label:'Revenue (ZAR)',data:series.map(x=>Number(x.value||0)),borderColor:'#0d6547',backgroundColor:'rgba(13,101,71,.12)',fill:true,tension:.38,pointRadius:3,pointHoverRadius:6}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>fmtMoney(c.raw)}}},scales:{x:{grid:{display:false}},y:{beginAtZero:true,ticks:{callback:v=>'R '+Number(v).toLocaleString('en-ZA')},grid:{color:'rgba(107,118,111,.13)'}}}}});
}
window.exportChart=()=>{if(!revenueChart)return toast('No chart available',false);const a=document.createElement('a');a.download='farmlink-revenue-trend.png';a.href=revenueChart.toBase64Image();a.click()};

function enhanceTables(scope=document){
  scope?.querySelectorAll?.('.table').forEach(table=>{
    if(table.dataset.enhanced)return;table.dataset.enhanced='true';
    const wrapper=table.closest('.table-wrap,.panel');
    if(wrapper){const tools=document.createElement('div');tools.className='table-tools';tools.innerHTML='<button type="button">Export CSV</button>';tools.querySelector('button').onclick=()=>exportTableCSV(table);wrapper.insertBefore(tools,table);}
    table.querySelectorAll('th').forEach((th,index)=>{if(!th.textContent.trim())return;th.classList.add('sortable');th.onclick=()=>sortTable(table,index,th)});
  });
}
function sortTable(table,index,th){const body=table.tBodies[0];if(!body)return;const asc=!th.classList.contains('sort-asc');table.querySelectorAll('th').forEach(x=>x.classList.remove('sort-asc','sort-desc'));th.classList.add(asc?'sort-asc':'sort-desc');[...body.rows].sort((a,b)=>{const av=a.cells[index]?.innerText.trim()||'',bv=b.cells[index]?.innerText.trim()||'';const an=Number(av.replace(/[^0-9.-]/g,'')),bn=Number(bv.replace(/[^0-9.-]/g,''));const cmp=!Number.isNaN(an)&&!Number.isNaN(bn)?an-bn:av.localeCompare(bv,undefined,{numeric:true});return asc?cmp:-cmp}).forEach(r=>body.appendChild(r))}
function exportTableCSV(table){const rows=[...table.rows].map(row=>[...row.cells].map(cell=>'"'+cell.innerText.replaceAll('"','""').trim()+'"').join(','));const blob=new Blob([rows.join('\n')],{type:'text/csv'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='farmlink-export-'+new Date().toISOString().slice(0,10)+'.csv';a.click();URL.revokeObjectURL(url)}
const tableObserver=new MutationObserver(()=>enhanceTables(document));tableObserver.observe(document.querySelector('main'),{subtree:true,childList:true});

function setupTheme(){const saved=localStorage.getItem('farmlink_theme');if(saved==='dark')document.body.classList.add('dark');$('#themeToggle').onclick=()=>{document.body.classList.toggle('dark');localStorage.setItem('farmlink_theme',document.body.classList.contains('dark')?'dark':'light')}}
function setupGlobalSearch(){const overlay=$('#globalSearch'),input=$('#globalSearchInput'),results=$('#globalSearchResults');const open=()=>{overlay.classList.remove('hidden');setTimeout(()=>input.focus(),20)},close=()=>overlay.classList.add('hidden');$('#globalSearchTrigger').onclick=open;overlay.onclick=e=>{if(e.target===overlay)close()};input.oninput=debounce(async()=>{const q=input.value.trim();if(q.length<2){results.innerHTML='<div class="search-hint">Enter at least two characters.</div>';return}results.innerHTML='<div class="search-hint">Searching FarmLink...</div>';try{const resources=['farmers','buyers','orders','memberships'];const responses=await Promise.all(resources.map(r=>api(`/admin/${r}?q=${encodeURIComponent(q)}&status=all`).catch(()=>({items:[]}))));const items=responses.flatMap((r,i)=>(r.items||[]).map(x=>({...x,_resource:resources[i]}))).slice(0,30);results.innerHTML=items.length?items.map(x=>`<div class="search-result" data-resource="${x._resource}" data-id="${x.id}"><div><strong>${esc(nameOf(x))}</strong><span>${esc(x.reference||'')} \u00B7 ${esc(x._resource)}</span></div>${badge(x.status||'Record')}</div>`).join(''):'<div class="search-hint">No matching records.</div>';results.querySelectorAll('.search-result').forEach(row=>row.onclick=()=>{close();showView(row.dataset.resource);setTimeout(()=>openRecord(row.dataset.resource,Number(row.dataset.id)),250)})}catch(e){results.innerHTML=`<div class="search-hint">${esc(e.message)}</div>`}},280);document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();open()}if(e.key==='Escape')close()})}
async function loadNotificationMenu(){try{const rows=await api('/admin/notifications');const recent=rows.slice(0,8),badgeEl=$('#notificationBadge');badgeEl.textContent=recent.length;badgeEl.classList.toggle('hidden',!recent.length);$('#notificationList').innerHTML=recent.length?recent.map(x=>`<div class="notification-item"><i class="notification-dot"></i><div><strong>${esc(x.subject||x.channel+' notification')}</strong><span>${esc(x.recipient)} \u00B7 ${fmtDate(x.sent_at||x.created_at)}</span></div></div>`).join(''):'<div class="search-hint">No notifications.</div>'}catch{$('#notificationList').innerHTML='<div class="search-hint">Unable to load notifications.</div>'}}
function setupNotifications(){const menu=$('#notificationDropdown');$('#notificationToggle').onclick=async()=>{menu.classList.toggle('hidden');if(!menu.classList.contains('hidden'))await loadNotificationMenu()};$('#markNotificationsRead').onclick=()=>{$('#notificationBadge').classList.add('hidden');menu.classList.add('hidden')};document.addEventListener('click',e=>{if(!e.target.closest('.notification-menu'))menu.classList.add('hidden')})}
function setupShortcuts(){document.addEventListener('keydown',e=>{if(e.target.matches('input,textarea,select'))return;if(e.key.toLowerCase()==='o')showView('orders');if(e.key.toLowerCase()==='i')showView('finance')})}

installIcons();setupTheme();setupGlobalSearch();setupNotifications();setupShortcuts();
if(token)start();

