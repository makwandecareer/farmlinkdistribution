const API = (() => {
  const configured = window.FARMLINK_API_URL?.trim();
  if (configured) return configured.replace(/\/$/, '') + '/api';
  if (['localhost','127.0.0.1'].includes(window.location.hostname)) return 'http://localhost:8000/api';
  return 'https://farmlinkdistribution.onrender.com/api';
})();
const get = id => document.getElementById(id);
const value = id => get(id)?.value?.trim() || '';

const menuButton = document.querySelector('.menu-button');
const nav = document.querySelector('.main-nav');
menuButton?.addEventListener('click', () => { const open = menuButton.getAttribute('aria-expanded') === 'true'; menuButton.setAttribute('aria-expanded', String(!open)); nav.classList.toggle('open', !open); });
nav?.querySelectorAll('a').forEach(a => a.addEventListener('click', () => nav.classList.remove('open')));

const tabs=[...document.querySelectorAll('.tab')], panels=[...document.querySelectorAll('.form-panel')];
function activateTab(name){tabs.forEach(t=>t.classList.toggle('active',t.dataset.tab===name));panels.forEach(p=>p.classList.toggle('active',p.dataset.panel===name));}
tabs.forEach(t=>t.addEventListener('click',()=>activateTab(t.dataset.tab)));
document.querySelectorAll('[data-open-tab]').forEach(a=>a.addEventListener('click',()=>{activateTab(a.dataset.openTab);if(a.dataset.plan&&get('membershipPlan'))get('membershipPlan').value=a.dataset.plan;}));
if(get('requiredDate')) get('requiredDate').min=new Date().toISOString().split('T')[0];

const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');observer.unobserve(e.target)}}),{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>observer.observe(el));

function notify(message, ok=true){
  let box=get('siteToast');
  if(!box){box=document.createElement('div');box.id='siteToast';box.style.cssText='position:fixed;right:20px;bottom:20px;z-index:9999;max-width:420px;padding:16px 20px;border-radius:12px;color:white;font-weight:700;box-shadow:0 18px 50px rgba(0,0,0,.25);transition:.25s';document.body.appendChild(box)}
  box.textContent=message;box.style.background=ok?'#0b6b49':'#a62b2b';box.style.opacity='1';setTimeout(()=>box.style.opacity='0',5000);
}
async function submit(endpoint,payload,form){
  const button=form.querySelector('button[type=submit]'), old=button.textContent;button.disabled=true;button.textContent='Submitting…';
  try{const r=await fetch(API+endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await r.json();if(!r.ok)throw new Error(Array.isArray(d.detail)?d.detail.map(x=>x.msg).join(', '):(d.detail||'Submission failed'));form.reset();notify(`Submitted successfully. Reference: ${d.reference}`);return d;}catch(e){notify(e.message,false)}finally{button.disabled=false;button.textContent=old}
}
get('farmerForm')?.addEventListener('submit',e=>{e.preventDefault();submit('/public/farmers',{farm_name:value('farmName'),contact_person:value('farmerContact'),phone:value('farmerPhone'),email:value('farmerEmail')||null,location:value('farmLocation'),producer_type:value('producerType'),weekly_capacity:Number(value('weeklyCapacity')),egg_sizes:value('farmerEggSizes'),packaging:value('farmerPackaging')||null,delivery_capability:value('deliveryCapability'),notes:value('farmerNotes')||null},e.currentTarget)});
get('buyerForm')?.addEventListener('submit',e=>{e.preventDefault();submit('/public/buyers',{business_name:value('buyerBusiness'),contact_person:value('buyerContact'),phone:value('buyerPhone'),email:value('buyerEmail'),category:value('buyerType'),location:value('buyerLocation'),weekly_volume:value('buyerVolume'),egg_size:value('buyerEggSize')||null,packaging:value('buyerPackaging')||null,frequency:value('buyerFrequency'),notes:value('buyerNotes')||null},e.currentTarget)});
get('orderForm')?.addEventListener('submit',e=>{e.preventDefault();submit('/public/orders',{business_name:value('businessName'),contact_person:value('contactPerson'),phone:value('phone'),email:value('email')||null,customer_type:value('customerType'),delivery_area:value('location'),egg_size:value('eggSize'),packaging:value('packaging'),quantity:value('quantity'),frequency:value('frequency'),required_date:value('requiredDate'),notes:value('notes')||null},e.currentTarget)});
get('membershipForm')?.addEventListener('submit',e=>{e.preventDefault();submit('/public/memberships',{applicant_type:value('membershipApplicantType'),selected_service:value('membershipPlan'),business_name:value('membershipBusiness'),contact_person:value('membershipContact'),phone:value('membershipPhone'),email:value('membershipEmail'),location:value('membershipLocation'),preferred_payment_method:value('membershipPayment'),notes:value('membershipNotes')||null},e.currentTarget)});
