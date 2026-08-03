FarmLink Paystack End-to-End Integration

This package completes the payment lifecycle:

1. Server-side transaction initialization
2. Paystack checkout URL generation
3. Callback verification
4. Signed webhook validation using HMAC SHA-512
5. Exact amount and ZAR currency validation
6. Idempotent Payment record creation
7. Order, membership, or invoice reconciliation
8. Audit-trail entries
9. Receipt notification queue
10. Downloadable PDF receipt
11. Manual Finance reconciliation endpoint
12. Payment Records visibility in the admin portal

Important Render environment variables:

PAYSTACK_PUBLIC_KEY=pk_test_...
PAYSTACK_SECRET_KEY=sk_test_...
PAYSTACK_CALLBACK_URL=https://farmlinkdistribution.onrender.com/api/payments/paystack/callback
PUBLIC_BASE_URL=https://farmlinkdistribution.onrender.com

Paystack Webhook URL:

https://farmlinkdistribution.onrender.com/api/payments/paystack/webhook

Deployment:

Copy backend/app/operations.py and backend/app/main.py into the project.
Then run:

git add backend/app/operations.py backend/app/main.py backend/tests/test_paystack_workflow.py
git commit -m "Complete Paystack payment reconciliation workflow"
git push origin main

Keep Test Mode enabled until successful, failed, abandoned, duplicate-webhook,
amount-mismatch, and callback tests have all passed.
