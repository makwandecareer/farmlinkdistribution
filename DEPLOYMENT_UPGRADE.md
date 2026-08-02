# FarmLink Platform v2 — Render Deployment Upgrade

## What this upgrade adds

- World-class, fully responsive administration interface with absolute asset paths.
- Executive analytics: daily/monthly revenue, order volume, active suppliers/buyers, supplier and customer rankings, province coverage, membership growth and delivery performance.
- Inventory lots by farmer, size, packaging, quantity, price and expiry.
- Vehicles, drivers, dispatch scheduling and delivery tracking.
- Quality cases, affected stock, severity, findings and corrective action.
- Invoices with downloadable PDF documents and outstanding balances.
- Supplier-payment records and partial-payment visibility.
- Paystack server-side transaction initialisation, verification and signed webhook processing.
- Refund records.
- Secure proof-of-payment and compliance-document storage inside PostgreSQL (maximum 10 MB per file).
- Email notification queue with SMTP delivery.
- Fine-grained administrator roles: ADMIN, FINANCE, OPERATIONS, LOGISTICS and QUALITY.
- Forced temporary-password changes and failed-login throttling.

## Replace the repository files

Extract this package over the existing repository, preserving your private `.env` values. Then run:

```bat
git add .
git commit -m "Upgrade FarmLink operations platform and administration centre"
git push origin main
```

Render should redeploy the backend and static site automatically.

## Backend environment variables on Render

Keep all existing values and add:

```text
PAYSTACK_PUBLIC_KEY=pk_test_...
PAYSTACK_SECRET_KEY=sk_test_...
PAYSTACK_CALLBACK_URL=https://farmlinkdistribution-1ndv.onrender.com/payment/callback
SMTP_HOST=your-smtp-host
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=notifications@your-domain.co.za
```

Set CORS to include the live static site:

```text
CORS_ORIGINS=https://farmlinkdistribution-1ndv.onrender.com
```

Never place secret keys in `frontend/`.

## Paystack dashboard URLs

```text
Callback URL:
https://farmlinkdistribution-1ndv.onrender.com/payment/callback

Webhook URL:
https://farmlinkdistribution.onrender.com/api/payments/paystack/webhook
```

Use test mode until a complete payment has been initialised, paid, received by the webhook and verified by the backend.

## Database

The application uses `Base.metadata.create_all()` at startup. The upgrade adds new tables without deleting existing records. PostgreSQL remains the source of truth.

## Admin URLs

```text
Website: https://farmlinkdistribution-1ndv.onrender.com
Admin:   https://farmlinkdistribution-1ndv.onrender.com/admin/
API:     https://farmlinkdistribution.onrender.com/docs
```

After deployment, hard refresh the admin page with `Ctrl+Shift+R` so the browser loads `admin.css?v=2.0` and `admin.js?v=2.0`.

## External services still requiring provider accounts

Email delivery works after SMTP credentials are configured. SMS and WhatsApp messages are recorded in the communications queue, but actual delivery requires an approved provider account and credentials. The platform does not pretend that a queued SMS or WhatsApp message was sent.
