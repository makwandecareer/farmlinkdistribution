FarmLink Backend — Payment Records Route Fix

The Payment Records screen returned 404 because the static route:

    GET /api/admin/payments

was declared below the generic route:

    GET /api/admin/{resource}

FastAPI/Starlette resolves routes in declaration order, so "payments" was
captured as the generic resource name.

This patch moves all payment routes above the generic resource routes:

    GET   /api/admin/payments
    POST  /api/admin/payments
    PATCH /api/admin/payments/{payment_id}

The previous Users and Audit route fixes are retained.

Replace backend/app/main.py, commit, push, and wait for the Render backend
service to redeploy.
