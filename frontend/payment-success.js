const API = (() => {
  const configured = window.FARMLINK_API_URL?.trim();
  if (configured) return configured.replace(/\/$/, '') + '/api';
  if (['localhost','127.0.0.1'].includes(location.hostname)) return 'http://localhost:8000/api';
  return 'https://farmlinkdistribution.onrender.com/api';
})();

const params = new URLSearchParams(location.search);
const reference = params.get('reference') || params.get('trxref');
const card = document.getElementById('paymentCard');
const title = document.getElementById('statusTitle');
const message = document.getElementById('statusMessage');
const icon = document.getElementById('statusIcon');
const details = document.getElementById('paymentDetails');

function money(value, currency='ZAR') {
  return new Intl.NumberFormat('en-ZA', {style:'currency', currency}).format(Number(value || 0));
}

function render(result) {
  details.hidden = false;
  document.getElementById('referenceValue').textContent = result.reference || reference || '—';
  document.getElementById('statusValue').textContent = result.status || 'Unknown';
  document.getElementById('amountValue').textContent = money(result.amount, result.currency || 'ZAR');
  document.getElementById('channelValue').textContent = result.channel || 'Paystack';

  if (result.verified) {
    icon.textContent = '✓';
    title.textContent = 'Payment verified';
    message.textContent = 'Your payment was confirmed securely. FarmLink has updated the relevant account and payment records.';
    return;
  }

  card.classList.add('pending');
  icon.textContent = '…';
  title.textContent = 'Payment not completed';
  message.textContent = `Current status: ${result.status || 'Pending'}. No service will be activated until Paystack confirms the payment.`;
}

async function verify() {
  if (!reference) {
    card.classList.add('error');
    icon.textContent = '!';
    title.textContent = 'Missing payment reference';
    message.textContent = 'The callback did not contain a Paystack reference. Please contact FarmLink support.';
    return;
  }

  try {
    const response = await fetch(`${API}/payments/paystack/verify/${encodeURIComponent(reference)}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || 'Verification failed');
    render(data);
  } catch (error) {
    card.classList.add('error');
    icon.textContent = '!';
    title.textContent = 'We could not verify the payment';
    message.textContent = `${error.message}. Do not make another payment until FarmLink confirms the transaction.`;
  }
}

verify();
