const API = (() => {
  const configured = window.FARMLINK_API_URL?.trim();
  if (configured) return configured.replace(/\/$/, '') + '/api';
  if (['localhost', '127.0.0.1'].includes(location.hostname)) return 'http://localhost:8000/api';
  return 'https://farmlinkdistribution.onrender.com/api';
})();

const get = id => document.getElementById(id);
const value = id => get(id)?.value?.trim() || '';
const menuButton = document.querySelector('.menu-button');
const nav = document.querySelector('.main-nav');

const scrim = document.createElement('div');
scrim.className = 'nav-scrim';
document.body.appendChild(scrim);

function setMenu(open) {
  if (!menuButton || !nav) return;
  menuButton.setAttribute('aria-expanded', String(open));
  nav.classList.toggle('open', open);
  document.body.classList.toggle('nav-open', open);
  if (open) nav.querySelector('a')?.focus({preventScroll:true});
}

menuButton?.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
scrim.addEventListener('click', () => setMenu(false));
nav?.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setMenu(false)));
document.addEventListener('keydown', e => { if (e.key === 'Escape') setMenu(false); });
window.addEventListener('resize', () => { if (window.innerWidth > 900) setMenu(false); }, {passive:true});

const tabs = [...document.querySelectorAll('.tab')];
const panels = [...document.querySelectorAll('.form-panel')];
function activateTab(name) {
  tabs.forEach(t => {
    const active = t.dataset.tab === name;
    t.classList.toggle('active', active);
    t.setAttribute('aria-selected', String(active));
    t.setAttribute('tabindex', active ? '0' : '-1');
  });
  panels.forEach(p => {
    const active = p.dataset.panel === name;
    p.classList.toggle('active', active);
    p.hidden = !active;
  });
}
tabs.forEach((t, i) => {
  t.setAttribute('role', 'tab');
  t.addEventListener('click', () => activateTab(t.dataset.tab));
  t.addEventListener('keydown', e => {
    if (!['ArrowLeft','ArrowRight'].includes(e.key)) return;
    e.preventDefault();
    const next = e.key === 'ArrowRight' ? (i + 1) % tabs.length : (i - 1 + tabs.length) % tabs.length;
    tabs[next].focus();
    activateTab(tabs[next].dataset.tab);
  });
});
document.querySelectorAll('[data-open-tab]').forEach(a => a.addEventListener('click', () => {
  activateTab(a.dataset.openTab);
  if (a.dataset.plan && get('membershipPlan')) get('membershipPlan').value = a.dataset.plan;
}));
activateTab(document.querySelector('.tab.active')?.dataset.tab || 'farmer');

if (get('requiredDate')) get('requiredDate').min = new Date().toISOString().split('T')[0];

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target); }
  }), {threshold:.12, rootMargin:'0px 0px -40px'});
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
} else {
  document.querySelectorAll('.reveal').forEach(el => el.classList.add('visible'));
}

function notify(message, ok = true) {
  let box = get('siteToast');
  if (!box) {
    box = document.createElement('div');
    box.id = 'siteToast';
    box.setAttribute('role', 'status');
    box.setAttribute('aria-live', 'polite');
    box.style.cssText = 'position:fixed;right:max(18px,env(safe-area-inset-right));bottom:max(18px,env(safe-area-inset-bottom));z-index:9999;max-width:min(420px,calc(100vw - 36px));padding:16px 20px;border-radius:12px;color:white;font-weight:700;box-shadow:0 18px 50px rgba(0,0,0,.25);transition:.25s;line-height:1.45';
    document.body.appendChild(box);
  }
  box.textContent = message;
  box.style.background = ok ? '#0b6b49' : '#a62b2b';
  box.style.opacity = '1';
  clearTimeout(box._timer);
  box._timer = setTimeout(() => box.style.opacity = '0', 5000);
}

function focusFirstInvalid(form) {
  const invalid = form.querySelector(':invalid');
  if (invalid) {
    invalid.focus({preventScroll:true});
    invalid.scrollIntoView({behavior:'smooth', block:'center'});
  }
}

async function submit(endpoint, payload, form) {
  if (!form.reportValidity()) { focusFirstInvalid(form); return; }
  const button = form.querySelector('button[type=submit]');
  const old = button.textContent;
  button.disabled = true;
  button.setAttribute('aria-busy', 'true');
  button.textContent = 'Submitting…';
  try {
    if (!navigator.onLine) throw new Error('You appear to be offline. Please reconnect and try again.');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    const r = await fetch(API + endpoint, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload),
      signal:controller.signal
    });
    clearTimeout(timeout);
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(Array.isArray(d.detail) ? d.detail.map(x => x.msg).join(', ') : (d.detail || 'Submission failed'));
    form.reset();
    notify(`Submitted successfully. Reference: ${d.reference}`);
    return d;
  } catch (e) {
    notify(e.name === 'AbortError' ? 'The request timed out. Please try again.' : e.message, false);
  } finally {
    button.disabled = false;
    button.removeAttribute('aria-busy');
    button.textContent = old;
  }
}

get('farmerForm')?.addEventListener('submit', e => { e.preventDefault(); submit('/public/farmers', {farm_name:value('farmName'),contact_person:value('farmerContact'),phone:value('farmerPhone'),email:value('farmerEmail')||null,location:value('farmLocation'),producer_type:value('producerType'),weekly_capacity:Number(value('weeklyCapacity')),egg_sizes:value('farmerEggSizes'),packaging:value('farmerPackaging')||null,delivery_capability:value('deliveryCapability'),notes:value('farmerNotes')||null}, e.currentTarget); });
get('buyerForm')?.addEventListener('submit', e => { e.preventDefault(); submit('/public/buyers', {business_name:value('buyerBusiness'),contact_person:value('buyerContact'),phone:value('buyerPhone'),email:value('buyerEmail'),category:value('buyerType'),location:value('buyerLocation'),weekly_volume:value('buyerVolume'),egg_size:value('buyerEggSize')||null,packaging:value('buyerPackaging')||null,frequency:value('buyerFrequency'),notes:value('buyerNotes')||null}, e.currentTarget); });
get('orderForm')?.addEventListener('submit', e => { e.preventDefault(); submit('/public/orders', {business_name:value('businessName'),contact_person:value('contactPerson'),phone:value('phone'),email:value('email')||null,customer_type:value('customerType'),delivery_area:value('location'),egg_size:value('eggSize'),packaging:value('packaging'),quantity:value('quantity'),frequency:value('frequency'),required_date:value('requiredDate'),notes:value('notes')||null}, e.currentTarget); });
get('membershipForm')?.addEventListener('submit', e => { e.preventDefault(); submit('/public/memberships', {applicant_type:value('membershipApplicantType'),selected_service:value('membershipPlan'),business_name:value('membershipBusiness'),contact_person:value('membershipContact'),phone:value('membershipPhone'),email:value('membershipEmail'),location:value('membershipLocation'),preferred_payment_method:value('membershipPayment'),notes:value('membershipNotes')||null}, e.currentTarget); });

window.addEventListener('offline', () => notify('You are offline. Form submissions will be available when your connection returns.', false));
window.addEventListener('online', () => notify('Connection restored. You can continue.'));
