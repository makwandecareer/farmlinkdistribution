FarmLink Administration Centre V4

This package replaces only:
  frontend/admin/
  frontend/assets/

Included upgrades:
- Live Chart.js revenue chart with PNG export
- Global search across farmers, buyers, orders and memberships (Ctrl+K)
- Live notifications dropdown
- Dark mode with saved preference
- Executive quick actions and expanded KPIs
- Smart empty states and skeleton loading
- Sortable tables and CSV export
- Professional SVG navigation icons
- Keyboard shortcuts: O orders, I finance
- Existing inventory, logistics, quality, finance, documents, communications, users and audit modules preserved

Install from E:\farmlink-production after extracting this ZIP:
  xcopy frontend frontend /E /I /Y
  git add frontend\admin frontend\assets
  git commit -m "Upgrade FarmLink admin to V4 enterprise dashboard"
  git push origin main

After Render deploys, open:
  https://farmlinkdistribution-1ndv.onrender.com/admin/

Then press Ctrl+Shift+R.

The admin page references Chart.js from jsDelivr. If your organisation blocks third-party CDNs, download Chart.js locally and change the script reference in frontend/admin/index.html.
