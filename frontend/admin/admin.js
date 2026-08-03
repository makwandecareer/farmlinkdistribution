const API=(()=>{const c=window.FARMLINK_API_URL?.trim();if(c)return c.replace(/\/$/,'')+'/api';if(['localhost','127.0.0.1'].includes(location.hostname))return'http://localhost:8000/api';return'https://farmlinkdistribution.onrender.com/api'})();
let token=localStorage.getItem('farmlink_token')||'',currentUser=null;
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??'—').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const fmtMoney=v=>new Intl.NumberFormat('en-ZA',{style:'currency',currency:'ZAR'}).format(Number(v||0));
const fmtDate=v=>v?new Date(v).toLocaleDateString('en-ZA'):'—';
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
async function start(){try{currentUser=currentUser||await api('/auth/me');$('#loginScreen').classList.add('hidden');$('#app').classList.remove('hidden');$('#sideName').textContent=currentUser.full_name;$('#sideRole').textContent=currentUser.job_title;const initials=currentUser.full_name.split(' ').map(x=>x[0]).slice(0,2).join('');$('#avatar').textContent=initials;$('#topAvatar').textContent=initials;$('#topName').textContent=currentUser.full_name;$('#topRole').textContent=`${currentUser.job_title||'Administrator'} · ${String(currentUser.role||'ADMIN').toUpperCase()}`;$('#usersNav').style.display=isCEO()?'flex':'none';if(currentUser.must_change_password)setTimeout(openPasswordModal,300);await showView('dashboard')}catch(e){logout()}}
const titles={dashboard:'Executive overview',farmers:'Farmer applications',buyers:'Business buyers',orders:'Bulk orders',memberships:'Memberships & marketing',inventory:'Inventory management',logistics:'Logistics & dispatch',quality:'Quality control',finance:'Finance centre',payments:'Payment records',notifications:'Communications',documents:'Document centre',users:'Administrator management',audit:'Audit trail'};
$$('#nav button').forEach(b=>b.onclick=()=>showView(b.dataset.view));$('#refresh').onclick=()=>showView($('.view.active').id);
async function showView(name){$$('#nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===name));$$('.view').forEach(v=>v.classList.toggle('active',v.id===name));$('#pageTitle').textContent=titles[name]||name;const loaders={dashboard:loadDashboard,farmers:()=>loadResource('farmers'),buyers:()=>loadResource('buyers'),orders:()=>loadResource('orders'),memberships:()=>loadResource('memberships'),inventory:loadInventory,logistics:loadLogistics,quality:loadQuality,finance:loadFinance,payments:loadPayments,notifications:loadNotifications,documents:loadDocuments,users:loadUsers,audit:loadAudit};try{await loaders[name]?.()}catch(e){toast(e.message,false)}}
const badge=s=>`<span class="status ${esc(String(s).replaceAll(' ','-'))}">${esc(s)}</span>`;
const empty=(m='No records available.',detail='New activity will appear here automatically.')=>`<div class="empty-state"><div><div class="empty-icon">✓</div><strong>${esc(m)}</strong><p>${esc(detail)}</p></div></div>`;
function bars(series){const max=Math.max(...series.map(x=>Number(x.value)),1);return `<div class="chart">${series.map(x=>`<div class="chart-col"><div class="chart-bar" style="height:${Math.max(4,Number(x.value)/max*180)}px" title="${esc(x.value)}"></div><span>${esc(x.label)}</span></div>`).join('')}</div>`}
async function loadDashboard(){const [d,a]=await Promise.all([api('/admin/dashboard'),api('/admin/analytics')]);const c=d.counts;$('#dashboard').innerHTML=`<div class="command-banner"><div><span class="kicker light">Operations command</span><h2>National distribution oversight from one accountable system.</h2><p>Monitor registrations, revenue, supply, fulfilment, quality and team activity in real time.</p></div><div class="command-date"><strong>${new Intl.DateTimeFormat('en-ZA',{dateStyle:'full'}).format(new Date())}</strong><span>Gauteng headquarters · Nationwide coordination</span></div></div>
<div class="quick-actions"><button class="quick-action" onclick="showView('farmers')"><span class="qa-icon">＋</span><span><strong>Review farmers</strong><span>Supplier approvals</span></span></button><button class="quick-action" onclick="showView('buyers')"><span class="qa-icon">▣</span><span><strong>Review buyers</strong><span>Customer onboarding</span></span></button><button class="quick-action" onclick="showView('orders')"><span class="qa-icon">◎</span><span><strong>Manage orders</strong><span>Quotes and fulfilment</span></span></button><button class="quick-action" onclick="showView('finance')"><span class="qa-icon">R</span><span><strong>Create invoice</strong><span>Finance control</span></span></button><button class="quick-action" onclick="showView('logistics')"><span class="qa-icon">⇄</span><span><strong>Schedule dispatch</strong><span>Delivery planning</span></span></button></div><div class="metrics">${[['R','Today revenue',fmtMoney(a.today_revenue),'Verified payments'],['↗','Month revenue',fmtMoney(a.month_revenue),'Current calendar month'],['●','Eggs traded',Number(a.total_trays).toLocaleString('en-ZA')+' trays','Recorded order volume'],['♙','Active farmers',a.active_farmers,'Approved suppliers'],['✓','Delivery performance',a.delivery_performance+'%','Completed dispatches']].map(([i,l,v,s])=>`<article class="metric"><span class="metric-icon">${i}</span><span class="label">${l}</span><strong>${v}</strong><small>${s}</small></article>`).join('')}</div>
<div class="grid-2"><article class="panel"><div class="panel-head"><div><span class="kicker">Commercial performance</span><h3>Revenue trend</h3></div></div>${bars(a.revenue_series)}</article><article class="panel"><div class="panel-head"><div><span class="kicker">Buyer activity</span><h3>Top customers</h3></div></div><div class="rank-list">${a.top_buyers.length?a.top_buyers.map((x,i)=>`<div class="rank-item"><span class="rank-num">${i+1}</span><strong>${esc(x.name)}</strong><span>${x.orders} orders</span></div>`).join(''):empty()}</div></article></div>
<div class="grid-2" style="margin-top:18px"><article class="panel"><div class="panel-head"><div><span class="kicker">Order pipeline</span><h3>Latest submissions</h3></div></div>${d.latest.length?d.latest.map(x=>`<div class="list-item"><div><strong>${esc(nameOf(x))}</strong><div class="ref">${esc(x.reference)}</div></div><span>${esc(labelOf(x.type))}</span>${badge(x.status)}<button class="link-btn" onclick="openRecord('${plural(x.type)}',${x.id})">Review</button></div>`).join(''):empty()}</article><article class="panel"><div class="panel-head"><div><span class="kicker">Supplier strength</span><h3>Top capacity</h3></div></div><div class="rank-list">${a.top_suppliers.length?a.top_suppliers.map((x,i)=>`<div class="rank-item"><span class="rank-num">${i+1}</span><strong>${esc(x.name)}</strong><span>${Number(x.capacity).toLocaleString()} trays/wk</span></div>`).join(''):empty()}</div></article></div>`}
const plural=t=>t==='membership'?'memberships':t+'s',labelOf=t=>({farmer:'Farmer',buyer:'Buyer',order:'Order',membership:'Membership'})[t]||t,nameOf=r=>r.farm_name||r.business_name||r.payer_name||r.full_name||'Record';
const actionButtons=(resource,record)=>`<div class="row-actions"><button class="link-btn" onclick="openRecord('${resource}',${record.id})">Review</button><button class="approve-btn" onclick="quickDecision('${resource}',${record.id},'Approved')">Approve</button><button class="reject-btn" onclick="quickDecision('${resource}',${record.id},'Rejected')">Reject</button></div>`;
window.quickDecision=async(resource,id,status)=>{const verb=status==='Approved'?'approve':'reject';if(!confirm(`Are you sure you want to ${verb} this ${resource.slice(0,-1)} record?`))return;try{await api(`/admin/${resource}/${id}`,{method:'PATCH',body:JSON.stringify({status})});toast(`Record ${status.toLowerCase()}`);await loadResource(resource)}catch(err){toast(err.message,false)}};
const configs={farmers:{title:'Farmer applications',desc:'Verify supplier identity, capacity, location and delivery capability.',cols:['Supplier','Province','Location','Weekly capacity','Status','Assigned',''],row:r=>[`${esc(r.farm_name)}<div class="ref">${esc(r.reference)}</div>`,provinceBadge(r),esc(r.location),`${Number(r.weekly_capacity).toLocaleString()} trays`,badge(r.status),esc(r.assigned_to?.full_name||'Unassigned'),actionButtons('farmers',r)]},buyers:{title:'Business buyer registrations',desc:'Review commercial requirements and customer demand.',cols:['Buyer','Province','Category','Weekly demand','Status','Assigned',''],row:r=>[`${esc(r.business_name)}<div class="ref">${esc(r.reference)}</div>`,provinceBadge(r),esc(r.category),esc(r.weekly_volume),badge(r.status),esc(r.assigned_to?.full_name||'Unassigned'),actionButtons('buyers',r)]},orders:{title:'Bulk order requests',desc:'Confirm supply, quotations and fulfilment ownership.',cols:['Customer','Quantity','Required date','Status','Quoted',''],row:r=>[`${esc(r.business_name)}<div class="ref">${esc(r.reference)}</div>`,esc(r.quantity),fmtDate(r.required_date),badge(r.status),r.quoted_amount?fmtMoney(r.quoted_amount):'Not quoted',`<button class="link-btn" onclick="openRecord('orders',${r.id})">Manage</button>`]},memberships:{title:'Membership and marketing',desc:'Review premium subscriptions and campaign applications.',cols:['Applicant','Service','Location','Status','Assigned',''],row:r=>[`${esc(r.business_name)}<div class="ref">${esc(r.reference)}</div>`,esc(r.selected_service),esc(r.location),badge(r.status),esc(r.assigned_to?.full_name||'Unassigned'),`<button class="link-btn" onclick="openRecord('memberships',${r.id})">Review</button>`]}};
async function loadResource(resource){const cfg=configs[resource],v=$('#'+resource);v.innerHTML=`<div class="page-head"><div><span class="kicker">Central records</span><h2>${cfg.title}</h2><p class="muted">${cfg.desc}</p></div><div class="toolbar"><input id="${resource}Search" placeholder="Search records"><select id="${resource}Province">${provinceOptions()}</select><select id="${resource}Status"><option value="all">All statuses</option>${['Pending','Approved','In progress','Completed','Rejected','Cancelled'].map(x=>`<option>${x}</option>`).join('')}</select></div></div><div class="panel table-wrap"><div id="${resource}Table"></div></div>`;const render=async()=>{const d=await api(`/admin/${resource}?q=${encodeURIComponent($('#'+resource+'Search').value)}&status=${encodeURIComponent($('#'+resource+'Status').value)}`);const province=$('#'+resource+'Province')?.value||'all';const items=(d.items||[]).filter(r=>province==='all'||provinceOf(r)===province);$('#'+resource+'Table').innerHTML=items.length?table(cfg.cols,items.map(cfg.row)):empty('No matching records for this province and status.')};$('#'+resource+'Search').oninput=debounce(render,250);$('#'+resource+'Province').onchange=render;$('#'+resource+'Status').onchange=render;await render()}
const table=(cols,rows)=>`<table class="table"><thead><tr>${cols.map(c=>`<th>${c}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(c=>`<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
function debounce(fn,ms){let t;return()=>{clearTimeout(t);t=setTimeout(fn,ms)}}
window.openRecord=async(resource,id)=>{const [r,users]=await Promise.all([api(`/admin/${resource}/${id}`),api('/admin/users')]);const excluded=['id','assigned_to_id','internal_notes','created_at','updated_at','assigned_to'];const fields=Object.entries(r).filter(([k])=>!excluded.includes(k));if(!fields.some(([k])=>k==='province'))fields.splice(2,0,['province',provinceOf(r)]);$('#drawerBody').innerHTML=`<span class="kicker">${esc(resource.slice(0,-1))} record</span><h2>${esc(nameOf(r))}</h2><p class="ref">${esc(r.reference)}</p><div class="detail-grid">${fields.map(([k,v])=>`<div class="detail"><span>${esc(k.replaceAll('_',' '))}</span><strong>${esc(v)}</strong></div>`).join('')}</div><form id="recordForm"><div class="form-grid"><label>Status<select id="recordStatus">${['Pending','Approved','In progress','Completed','Rejected','Cancelled'].map(s=>`<option ${r.status===s?'selected':''}>${s}</option>`).join('')}</select></label><label>Assigned administrator<select id="recordOwner"><option value="">Unassigned</option>${users.filter(u=>u.is_active).map(u=>`<option value="${u.id}" ${r.assigned_to_id===u.id?'selected':''}>${esc(u.full_name)}</option>`).join('')}</select></label>${resource==='orders'?`<label>Quoted amount (R)<input id="quotedAmount" type="number" step="0.01" min="0" value="${r.quoted_amount||''}"></label>`:''}<label class="full">Internal notes<textarea id="internalNotes" rows="5">${esc(r.internal_notes||'')}</textarea></label></div><div class="form-actions"><button type="button" class="btn btn-secondary" onclick="closeDrawer()">Cancel</button><button class="btn btn-primary">Save changes</button></div></form>`;openDrawer();$('#recordForm').onsubmit=async e=>{e.preventDefault();const payload={status:$('#recordStatus').value,assigned_to_id:$('#recordOwner').value?Number($('#recordOwner').value):null,internal_notes:$('#internalNotes').value};if(resource==='orders')payload.quoted_amount=$('#quotedAmount').value?Number($('#quotedAmount').value):null;await api(`/admin/${resource}/${id}`,{method:'PATCH',body:JSON.stringify(payload)});toast('Record updated');closeDrawer();loadResource(resource)}};
async function loadInventory(){const rows=await api('/admin/inventory');$('#inventory').innerHTML=pageHead('Supply control','Inventory management','Track egg availability by farmer, size, packaging and expiry.',`<button class="btn btn-primary" onclick="openInventoryModal()">Add inventory lot</button>`)+`<div class="panel table-wrap">${rows.length?table(['Reference','Farmer','Egg size','Packaging','Available','Price','Status'],rows.map(r=>[esc(r.reference),esc(r.farmer_name),esc(r.egg_size),esc(r.packaging),`${r.trays_available} trays`,r.unit_price?fmtMoney(r.unit_price):'—',badge(r.status)])):empty()}</div>`}
window.openInventoryModal=async()=>{const farmers=(await api('/admin/farmers?status=Approved')).items;openForm('Add inventory lot',`<label>Farmer<select id="iFarmer" required>${farmers.map(x=>`<option value="${x.id}">${esc(x.farm_name)}</option>`).join('')}</select></label><label>Egg size<input id="iSize" required></label><label>Packaging<input id="iPack" required></label><label>Trays available<input id="iTrays" type="number" min="0" required></label><label>Unit price (R)<input id="iPrice" type="number" min="0" step=".01"></label><label>Status<select id="iStatus"><option>Available</option><option>Reserved</option><option>Sold</option><option>Expired</option></select></label>`,async()=>{await api('/admin/inventory',{method:'POST',body:JSON.stringify({farmer_id:+$('#iFarmer').value,egg_size:$('#iSize').value,packaging:$('#iPack').value,trays_available:+$('#iTrays').value,unit_price:$('#iPrice').value?+$('#iPrice').value:null,status:$('#iStatus').value})});loadInventory()})}
async function loadLogistics(){const [d,v]=await Promise.all([api('/admin/dispatches'),api('/admin/vehicles')]);$('#logistics').innerHTML=pageHead('National fulfilment','Logistics & dispatch','Schedule collections, assign vehicles and monitor delivery status.',`<button class="btn btn-secondary" onclick="openVehicleModal()">Add vehicle</button> <button class="btn btn-primary" onclick="openDispatchModal()">Schedule dispatch</button>`)+`<div class="grid-2"><div class="panel table-wrap">${d.length?table(['Dispatch','Order','Vehicle','Date','Trays','Status'],d.map(x=>[esc(x.reference),esc(x.order_reference),esc(x.vehicle_registration||x.driver_name),fmtDate(x.scheduled_date),x.trays,badge(x.status)])):empty('No dispatches scheduled.')}</div><div class="panel table-wrap">${v.length?table(['Registration','Type','Capacity','Driver','Status'],v.map(x=>[esc(x.registration),esc(x.vehicle_type),`${x.capacity_trays} trays`,esc(x.driver_name),badge(x.status)])):empty('No vehicles registered.')}</div></div>`}
window.openVehicleModal=()=>openForm('Add vehicle',`<label>Registration<input id="vReg" required></label><label>Vehicle type<input id="vType" required></label><label>Capacity (trays)<input id="vCap" type="number" min="0" required></label><label>Driver name<input id="vDriver"></label><label>Driver phone<input id="vPhone"></label><label>Status<select id="vStatus"><option>Available</option><option>In service</option><option>Maintenance</option></select></label>`,async()=>{await api('/admin/vehicles',{method:'POST',body:JSON.stringify({registration:$('#vReg').value,vehicle_type:$('#vType').value,capacity_trays:+$('#vCap').value,driver_name:$('#vDriver').value||null,driver_phone:$('#vPhone').value||null,status:$('#vStatus').value})});loadLogistics()});
window.openDispatchModal=async()=>{const [orders,vehicles]=await Promise.all([api('/admin/orders?status=Approved'),api('/admin/vehicles')]);openForm('Schedule dispatch',`<label>Order<select id="dOrder" required>${orders.items.map(x=>`<option value="${x.id}">${esc(x.reference)} · ${esc(x.business_name)}</option>`).join('')}</select></label><label>Vehicle<select id="dVehicle"><option value="">Unassigned</option>${vehicles.map(x=>`<option value="${x.id}">${esc(x.registration)}</option>`).join('')}</select></label><label>Collection location<input id="dFrom" required></label><label>Delivery location<input id="dTo" required></label><label>Scheduled date<input id="dDate" type="datetime-local" required></label><label>Trays<input id="dTrays" type="number" min="0" required></label>`,async()=>{await api('/admin/dispatches',{method:'POST',body:JSON.stringify({order_id:+$('#dOrder').value,vehicle_id:$('#dVehicle').value?+$('#dVehicle').value:null,collection_location:$('#dFrom').value,delivery_location:$('#dTo').value,scheduled_date:new Date($('#dDate').value).toISOString(),trays:+$('#dTrays').value})});loadLogistics()})}
async function loadQuality(){const rows=await api('/admin/quality-cases');$('#quality').innerHTML=pageHead('Product assurance','Quality control','Record inspections, damaged stock, non-conformances and corrective action.',`<button class="btn btn-primary" onclick="openQualityModal()">Open quality case</button>`)+`<div class="panel table-wrap">${rows.length?table(['Reference','Type','Severity','Trays affected','Status','Created'],rows.map(x=>[esc(x.reference),esc(x.case_type),badge(x.severity),x.trays_affected,badge(x.status),fmtDate(x.created_at)])):empty()}</div>`}
window.openQualityModal=()=>openForm('Open quality case',`<label>Case type<input id="qType" placeholder="Damaged stock, shell quality..." required></label><label>Severity<select id="qSeverity"><option>Low</option><option selected>Medium</option><option>High</option><option>Critical</option></select></label><label>Order ID<input id="qOrder" type="number" min="1"></label><label>Farmer ID<input id="qFarmer" type="number" min="1"></label><label>Trays affected<input id="qTrays" type="number" min="0" required></label><label class="full">Findings<textarea id="qFindings"></textarea></label>`,async()=>{await api('/admin/quality-cases',{method:'POST',body:JSON.stringify({case_type:$('#qType').value,severity:$('#qSeverity').value,order_id:$('#qOrder').value?+$('#qOrder').value:null,farmer_id:$('#qFarmer').value?+$('#qFarmer').value:null,trays_affected:+$('#qTrays').value,findings:$('#qFindings').value||null})});loadQuality()})
async function loadFinance(){const [inv,sp,tx,rf]=await Promise.all([api('/admin/invoices'),api('/admin/supplier-payments'),api('/admin/payment-transactions'),api('/admin/refunds')]);const outstanding=inv.reduce((s,x)=>s+Math.max(0,Number(x.total_amount)-Number(x.amount_paid)),0);$('#finance').innerHTML=pageHead('Financial governance','Finance centre','Invoices, supplier settlements, Paystack transactions, balances and refunds.',`<button class="btn btn-secondary" onclick="openSupplierPaymentModal()">Supplier payment</button> <button class="btn btn-primary" onclick="openInvoiceModal()">Create invoice</button>`)+`<div class="metrics"><article class="metric"><span class="label">Outstanding invoices</span><strong>${fmtMoney(outstanding)}</strong><small>${inv.filter(x=>x.status!=='Paid').length} open documents</small></article><article class="metric"><span class="label">Paystack transactions</span><strong>${tx.length}</strong><small>Server-verified records</small></article><article class="metric"><span class="label">Supplier payments</span><strong>${sp.length}</strong><small>Farmer settlements</small></article><article class="metric"><span class="label">Refund cases</span><strong>${rf.length}</strong><small>Controlled workflow</small></article></div><div class="grid-2"><div class="panel table-wrap">${inv.length?table(['Invoice','Customer','Total','Paid','Balance','Status','PDF'],inv.map(x=>[esc(x.reference),esc(x.customer_name),fmtMoney(x.total_amount),fmtMoney(x.amount_paid),fmtMoney(Number(x.total_amount)-Number(x.amount_paid)),badge(x.status),`<button class="link-btn" onclick="downloadFile('/admin/invoices/${x.id}/pdf','${esc(x.reference)}.pdf')">Download</button>`])):empty('No invoices created.')}</div><div class="panel table-wrap">${sp.length?table(['Reference','Farmer','Amount','Method','Status'],sp.map(x=>[esc(x.reference),esc(x.farmer_name),fmtMoney(x.amount),esc(x.method),badge(x.status)])):empty('No supplier payments.')}</div></div>`}
window.openInvoiceModal=()=>openForm('Create invoice',`<label>Related type<select id="fType"><option>order</option><option>membership</option></select></label><label>Record ID<input id="fEntity" type="number" min="1" required></label><label>Customer name<input id="fName" required></label><label>Customer email<input id="fEmail" type="email"></label><label>Subtotal (R)<input id="fSub" type="number" min="0" step=".01" required></label><label>Tax (R)<input id="fTax" type="number" min="0" step=".01" value="0"></label><label>Due date<input id="fDue" type="date" required></label><label class="full">Description<textarea id="fDesc" required></textarea></label>`,async()=>{await api('/admin/invoices',{method:'POST',body:JSON.stringify({entity_type:$('#fType').value,entity_id:+$('#fEntity').value,customer_name:$('#fName').value,customer_email:$('#fEmail').value||null,subtotal:+$('#fSub').value,tax_amount:+$('#fTax').value,due_date:$('#fDue').value,description:$('#fDesc').value})});loadFinance()});
window.openSupplierPaymentModal=async()=>{const farmers=(await api('/admin/farmers?status=Approved')).items;openForm('Record supplier payment',`<label>Farmer<select id="sFarmer">${farmers.map(x=>`<option value="${x.id}">${esc(x.farm_name)}</option>`).join('')}</select></label><label>Order ID<input id="sOrder" type="number" min="1"></label><label>Amount (R)<input id="sAmount" type="number" min=".01" step=".01" required></label><label>Method<select id="sMethod"><option>EFT</option><option>PayShap</option><option>Cash deposit</option></select></label><label>Bank reference<input id="sRef"></label><label>Status<select id="sStatus"><option>Pending</option><option>Approved</option><option>Paid</option><option>Failed</option></select></label>`,async()=>{await api('/admin/supplier-payments',{method:'POST',body:JSON.stringify({farmer_id:+$('#sFarmer').value,order_id:$('#sOrder').value?+$('#sOrder').value:null,amount:+$('#sAmount').value,method:$('#sMethod').value,bank_reference:$('#sRef').value||null,status:$('#sStatus').value})});loadFinance()})}
async function loadPayments(){
  const rows=await api('/admin/payments');
  const paid=rows.filter(x=>x.status==='Paid');
  const total=paid.reduce((s,x)=>s+Number(x.amount||0),0);
  const average=paid.length?total/paid.length:0;
  const methods={};
  paid.forEach(x=>methods[x.method]=(methods[x.method]||0)+Number(x.amount||0));
  const topMethod=Object.entries(methods).sort((a,b)=>b[1]-a[1])[0]?.[0]||'No verified payments';

  $('#payments').innerHTML=
    pageHead('Finance control','Payment records','Verified Paystack, Capitec EFT, PayShap, deposit and card records.',
      `<button class="btn btn-primary" onclick="openPaymentModal()">Add payment record</button>`)+
    `<div class="metrics payment-kpis">
      ${metricCard('Verified revenue',fmtMoney(total),'Paid records','R','emerald')}
      ${metricCard('Paid transactions',paid.length,'Successfully reconciled','✓','forest')}
      ${metricCard('Average transaction',fmtMoney(average),'Verified payments','↗','gold')}
      ${metricCard('Leading method',esc(topMethod),'By verified value','◉','blue')}
    </div>
    <div class="panel table-wrap">${rows.length?table(
      ['Reference','Payer','Amount','Method','Status','Entity','Date','Actions'],
      rows.map(r=>[
        esc(r.reference),
        esc(r.payer_name),
        fmtMoney(r.amount),
        esc(r.method),
        badge(r.status),
        `${esc(r.entity_type)} #${r.entity_id}`,
        fmtDate(r.created_at),
        `<div class="row-actions"><button class="link-btn" onclick="openPaymentDetail(${r.id})">View</button>${r.external_reference&&r.status==='Paid'?`<button class="link-btn" onclick="downloadFile('/payments/receipt/${esc(r.external_reference)}','${esc(r.reference)}-receipt.pdf')">Receipt</button>`:''}</div>`
      ])
    ):smartEmpty('No payment records yet','Verified Paystack and manually approved payments will appear here.','finance','Open finance centre')}</div>`;
}

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
  if(!confirm('Permanently remove this administrator? This action cannot be undone.'))return;
  try{
    await api(`/admin/users/${id}`,{method:'DELETE'});
    toast('Administrator removed');
    await loadUsers();
  }catch(err){toast(err.message,false)}
};
async function loadAudit(){
  const rows=await api('/admin/audit?limit=500');
  $('#audit').innerHTML=
    pageHead('Governance','Audit trail','Chronological record of access, approvals, finance activity and operational decisions.','')+
    `<div class="audit-toolbar toolbar">
      <input id="auditSearch" placeholder="Search actor, action or entity">
      <select id="auditAction"><option value="all">All activities</option>
        <option>Signed in</option><option>Created administrator</option><option>Activated administrator</option>
        <option>Suspended administrator</option><option>Removed administrator</option>
        <option>Approved</option><option>Rejected</option><option>Paystack payment</option>
      </select>
    </div><div id="auditTable" class="panel table-wrap"></div>`;
  const render=()=>{
    const q=$('#auditSearch').value.trim().toLowerCase();
    const action=$('#auditAction').value.toLowerCase();
    const filtered=rows.filter(r=>{
      const hay=`${r.actor_name||''} ${r.action||''} ${r.entity_type||''} ${r.entity_id||''}`.toLowerCase();
      const qok=!q||hay.includes(q);
      const aok=action==='all'||String(r.action||'').toLowerCase().includes(action);
      return qok&&aok;
    });
    $('#auditTable').innerHTML=filtered.length?table(
      ['Date','Actor','Action','Entity','IP address'],
      filtered.map(r=>[
        new Date(r.created_at).toLocaleString('en-ZA'),
        esc(r.actor_name),
        `<strong>${esc(r.action)}</strong>`,
        `${esc(r.entity_type)}${r.entity_id?' #'+r.entity_id:''}`,
        esc(r.ip_address||'—')
      ])
    ):empty('No audit records match the selected filters.');
  };
  $('#auditSearch').oninput=debounce(render,180);
  $('#auditAction').onchange=render;
  render();
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
  <div class="command-banner"><div><span class="kicker light">Operations command</span><h2>National distribution oversight from one accountable system.</h2><p>Monitor registrations, revenue, supply, fulfilment, quality and team activity in real time.</p></div><div class="command-date"><strong>${new Intl.DateTimeFormat('en-ZA',{dateStyle:'full'}).format(new Date())}</strong><span>Gauteng headquarters · Nationwide coordination</span></div></div>
  <div class="quick-actions">
    <button class="quick-action" data-jump="farmers"><b>+</b>Review farmers</button><button class="quick-action" data-jump="buyers"><b>+</b>Review buyers</button><button class="quick-action" data-jump="orders"><b>+</b>Manage orders</button><button class="quick-action" data-jump="finance"><b>R</b>Create invoice</button><button class="quick-action" data-jump="users"><b>+</b>Add administrator</button>
  </div>
  <div class="metrics">
    ${metricCard('Today revenue',fmtMoney(a.today_revenue),'Verified payments','R','emerald')}
    ${metricCard('Month revenue',fmtMoney(a.month_revenue),'Current calendar month','↗','forest')}
    ${metricCard('Eggs traded',Number(a.total_trays||0).toLocaleString('en-ZA')+' trays','Recorded order volume','◉','gold')}
    ${metricCard('Active farmers',a.active_farmers||0,'Approved suppliers','♙','blue')}
    ${metricCard('Delivery performance',(a.delivery_performance||0)+'%','Completed dispatches','⇄','teal')}
  </div>
  <div class="metrics secondary-metrics">
    ${metricCard('Pending farmers',pendingFarmers,'Awaiting approval','!')}
    ${metricCard('Pending buyers',pendingBuyers,'Awaiting approval','!')}
    ${metricCard('Open orders',openOrders,'Current pipeline','◎')}
    ${metricCard('Processed records',c.completed||0,'Completed workflow','✓')}
    ${metricCard('Membership activity',c.memberships?.pending||0,'Pending applications','◇')}
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
    const executive=await api('/admin/executive-summary').catch(()=>null);
    if(executive)$('#dashboard').insertAdjacentHTML('beforeend',nationalSummaryPanel(executive));
  }catch{}
  $$('.quick-action').forEach(b=>b.onclick=()=>{const view=b.dataset.jump;showView(view);if(view==='finance')setTimeout(()=>window.openInvoiceModal?.(),350);if(view==='users'&&isCEO())setTimeout(()=>window.openUserModal?.(),350)});
  drawRevenueChart(a.revenue_series||[]);
};
function metricCard(label,value,sub,icon,accent='green'){return `<article class="metric metric-${accent}"><span class="metric-icon">${icon}</span><span class="label">${label}</span><strong>${value}</strong><small>${sub}</small><span class="metric-trend">● Live data</span></article>`}

async function openPaymentDetail(id){
  try{
    const p=await api(`/admin/payments/${id}`);
    openDrawer(`<span class="kicker">Finance control</span><h2>${esc(p.reference)}</h2>
      <div class="detail-grid">
        ${detail('Payer',p.payer_name)}
        ${detail('Amount',fmtMoney(p.amount))}
        ${detail('Method',p.method)}
        ${detail('Status',p.status)}
        ${detail('External reference',p.external_reference||'—')}
        ${detail('Created',new Date(p.created_at).toLocaleString('en-ZA'))}
        ${detail('Entity',`${p.entity_type} #${p.entity_id}`)}
        ${detail('Notes',p.notes||'—')}
      </div>
      <div class="drawer-actions">
        ${p.receipt_url?`<button class="btn btn-primary" onclick="downloadFile('${p.receipt_url}','${esc(p.reference)}-receipt.pdf')">Download receipt</button>`:''}
        <button class="btn btn-secondary" onclick="showView('audit')">View audit trail</button>
      </div>`);
  }catch(e){toast(e.message,false)}
}
window.openPaymentDetail=openPaymentDetail;

function nationalSummaryPanel(summary){
  const national=summary.national||{};
  return `<article class="panel national-summary-panel">
    <div class="panel-head"><div><span class="kicker">CEO national command</span><h3>South African operating footprint</h3></div><span class="formal-badge">Live national summary</span></div>
    <div class="national-summary-grid">
      <div><span>Total farmers</span><strong>${Number(national.farmers||0).toLocaleString('en-ZA')}</strong></div>
      <div><span>Total buyers</span><strong>${Number(national.buyers||0).toLocaleString('en-ZA')}</strong></div>
      <div><span>Total orders</span><strong>${Number(national.orders||0).toLocaleString('en-ZA')}</strong></div>
      <div><span>Verified revenue</span><strong>${fmtMoney(national.paid_revenue||0)}</strong></div>
      <div><span>Pending approvals</span><strong>${Number(national.pending_approvals||0).toLocaleString('en-ZA')}</strong></div>
    </div>
    <div class="province-performance-table">
      ${table(['Province','Farmers','Buyers','Orders','Revenue'],(summary.provinces||[]).map(x=>[
        provinceBadge({province:x.province}),
        `${x.approved_farmers}/${x.farmers}`,
        `${x.approved_buyers}/${x.buyers}`,
        Number(x.orders||0).toLocaleString('en-ZA'),
        fmtMoney(x.revenue||0)
      ]))}
    </div>
  </article>`;
}
function provinceCoverage(rows){
  return `<article class="panel province-panel"><div class="panel-head"><div><span class="kicker">National footprint</span><h3>Provincial coverage</h3></div><span class="formal-badge">South Africa · 9 Provinces</span></div><div class="province-grid">${rows.map(x=>`<div class="province-card"><strong>${esc(x.province)}</strong><span>${x.farmers} farmers</span><span>${x.buyers} buyers</span></div>`).join('')}</div></article>`;
}
function smartEmpty(title,text,view,action){return `<div class="empty-action"><div class="empty-icon">＋</div><h4>${title}</h4><p>${text}</p><button class="btn btn-secondary" onclick="showView('${view}')">${action}</button></div>`}
function drawRevenueChart(series){
  const canvas=$('#revenueChart');if(!canvas)return;
  if(revenueChart)revenueChart.destroy();
  if(!window.Chart){canvas.replaceWith(Object.assign(document.createElement('div'),{className:'empty',textContent:'Chart library unavailable.'}));return}
  const hasData=series.some(x=>Number(x.value||0)!==0);
  if(!hasData){canvas.parentElement.innerHTML='<div class="chart-empty"><span class="chart-empty-icon">↗</span><strong>No revenue data yet</strong><p>Verified payments will appear here automatically.</p></div>';return;}
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
function setupGlobalSearch(){const overlay=$('#globalSearch'),input=$('#globalSearchInput'),results=$('#globalSearchResults');const open=()=>{overlay.classList.remove('hidden');setTimeout(()=>input.focus(),20)},close=()=>overlay.classList.add('hidden');$('#globalSearchTrigger').onclick=open;overlay.onclick=e=>{if(e.target===overlay)close()};input.oninput=debounce(async()=>{const q=input.value.trim();if(q.length<2){results.innerHTML='<div class="search-hint">Enter at least two characters.</div>';return}results.innerHTML='<div class="search-hint">Searching FarmLink...</div>';try{const resources=['farmers','buyers','orders','memberships'];const [responses,payments,users]=await Promise.all([
  Promise.all(resources.map(r=>api(`/admin/${r}?q=${encodeURIComponent(q)}&status=all`).catch(()=>({items:[]})))),
  api('/admin/payments').catch(()=>[]),
  isCEO()?api('/admin/users').catch(()=>[]):Promise.resolve([])
]);
const recordItems=responses.flatMap((r,i)=>(r.items||[]).map(x=>({...x,_resource:resources[i]})));
const paymentItems=(payments||[]).filter(x=>`${x.reference} ${x.payer_name} ${x.external_reference||''}`.toLowerCase().includes(q.toLowerCase())).map(x=>({...x,_resource:'payments',business_name:x.payer_name}));
const userItems=(users||[]).filter(x=>`${x.full_name} ${x.email} ${x.job_title}`.toLowerCase().includes(q.toLowerCase())).map(x=>({...x,_resource:'users',business_name:x.full_name,reference:x.email,status:x.is_active?'Approved':'Rejected'}));
const items=[...recordItems,...paymentItems,...userItems].slice(0,30);results.innerHTML=items.length?items.map(x=>`<div class="search-result" data-resource="${x._resource}" data-id="${x.id}"><div><strong>${esc(nameOf(x))}</strong><span>${esc(x.reference||'')} · ${esc(x._resource)}</span></div>${badge(x.status||'Record')}</div>`).join(''):'<div class="search-hint">No matching records.</div>';results.querySelectorAll('.search-result').forEach(row=>row.onclick=()=>{close();const resource=row.dataset.resource,id=Number(row.dataset.id);showView(resource);if(resource==='payments')setTimeout(()=>openPaymentDetail(id),250);else if(resource!=='users')setTimeout(()=>openRecord(resource,id),250)})}catch(e){results.innerHTML=`<div class="search-hint">${esc(e.message)}</div>`}},280);document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();open()}if(e.key==='Escape')close()})}
async function loadNotificationMenu(){try{const rows=await api('/admin/notifications');const recent=rows.slice(0,8),badgeEl=$('#notificationBadge');badgeEl.textContent=recent.length;badgeEl.classList.toggle('hidden',!recent.length);$('#notificationList').innerHTML=recent.length?recent.map(x=>`<div class="notification-item"><i class="notification-dot"></i><div><strong>${esc(x.subject||x.channel+' notification')}</strong><span>${esc(x.recipient)} · ${fmtDate(x.sent_at||x.created_at)}</span></div></div>`).join(''):'<div class="search-hint">No notifications.</div>'}catch{$('#notificationList').innerHTML='<div class="search-hint">Unable to load notifications.</div>'}}
function setupNotifications(){const menu=$('#notificationDropdown');$('#notificationToggle').onclick=async()=>{menu.classList.toggle('hidden');if(!menu.classList.contains('hidden'))await loadNotificationMenu()};$('#markNotificationsRead').onclick=()=>{$('#notificationBadge').classList.add('hidden');menu.classList.add('hidden')};document.addEventListener('click',e=>{if(!e.target.closest('.notification-menu'))menu.classList.add('hidden')})}
function setupShortcuts(){document.addEventListener('keydown',e=>{if(e.target.matches('input,textarea,select'))return;if(e.key.toLowerCase()==='o')showView('orders');if(e.key.toLowerCase()==='i')showView('finance')})}

installIcons();setupTheme();setupGlobalSearch();setupNotifications();setupShortcuts();
if(token)start();
