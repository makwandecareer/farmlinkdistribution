# FarmLink Production Platform

A full-stack FarmLink Distribution system with a public registration/order website and a secure administration backend.

## Included

- Farmer, buyer, bulk-order and membership APIs
- Central PostgreSQL or SQLite database
- CEO and administrator authentication
- CEO-only administrator creation, suspension and removal
- Record assignment, approval, rejection and internal notes
- Order quotation tracking
- Payment records for EFT, PayShap, card and other methods
- Audit logging
- Responsive public website and administration portal
- Docker deployment files
- Health endpoint and API documentation at `/docs`

## Important production note

This is deployable application code, but payment gateways, email/SMS delivery and POPIA legal documents require your actual provider accounts, verified business details and approved credentials. No real banking credentials are embedded.

## Local start with SQLite

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp ../.env.example .env
```

For quick local use, change `DATABASE_URL` in `.env` to:

```text
sqlite:///./data/farmlink.db
```

Set a strong `SECRET_KEY`, CEO email and temporary password, then run:

```bash
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- Website: `http://localhost:8000`
- Administration: `http://localhost:8000/admin`
- API documentation: `http://localhost:8000/docs`

## Docker production start

1. Copy `.env.example` to `.env`.
2. Set a strong `POSTGRES_PASSWORD`, `SECRET_KEY`, CEO email and CEO temporary password.
3. Run:

```bash
docker compose up -d --build
```

4. Place the application behind HTTPS using Cloudflare, Caddy, Nginx or your hosting provider.
5. Change the CEO temporary password after first login.

## CEO reset/creation

```bash
cd backend
PYTHONPATH=. python -m app.seed --email ceo@farmlinkdistribution.co.za --password 'StrongTemporaryPassword' --name 'Makwande Gcora'
```

## Security controls already included

- PBKDF2-SHA256 password hashing with per-user salts
- Signed expiring bearer tokens
- Role-based access control
- Protected CEO account
- Input validation
- Central audit trail
- No default credentials in source code

## Required before public launch

- Register and configure the production domain and HTTPS
- Replace `.env` secrets
- Configure daily encrypted database backups
- Add a transactional email provider for acknowledgements and password reset
- Add payment gateway credentials only after merchant approval
- Have POPIA privacy notice, terms, supplier terms and buyer terms reviewed
- Complete security testing and backup restoration testing
