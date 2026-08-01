FarmLink frontend-to-backend connection patch

Replace these files in your local repository:
- frontend/script.js
- frontend/admin/admin.js

Backend API configured:
https://farmlinkdistribution.onrender.com/api

After replacement:
1. git add frontend/script.js frontend/admin/admin.js
2. git commit -m "Connect frontend to live Render API"
3. git push origin main

In the Render backend environment, set CORS_ORIGINS to include the frontend URL after the frontend is deployed.
Example:
CORS_ORIGINS=https://farmlinkdistribution-web.onrender.com,http://localhost:8000,http://127.0.0.1:8000
