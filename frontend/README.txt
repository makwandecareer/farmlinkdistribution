FarmLink National Product SEO — GitHub Installer

Creates:
- /products/
- /products/eggs/
- /products/poultry/
- /products/potatoes/
- /products/onions/
- /products/tomatoes/
- /products/cabbage/
- /products/carrots/
- /products/spinach/
- /products/maize/
- /products/animal-feed/
- /products/fertilizer/
- /products/fresh-vegetables/
- /products/fresh-fruit/
- /products/livestock/
- /products/agricultural-inputs/

Each page includes:
- Unique title and meta description
- Canonical URL
- Open Graph and Twitter metadata
- Organization, CollectionPage, Breadcrumb and FAQ schema
- Google Analytics 4
- Responsive design
- Internal links across product categories
- Clear wording that availability and pricing require confirmation
- No fabricated prices, stock levels, farmer counts or delivery promises

The installer preserves existing sitemap URLs and adds the product pages.

Run:
powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\Downloads\FarmLink-National-Product-SEO-GitHub\install-product-seo.ps1"

Then:
cd /d E:\farmlink-production
git status
git add frontend\products frontend\sitemap.xml
git commit -m "Launch national agricultural product SEO pages"
git push origin main

After Render deploys:
- Test /products/ and /products/eggs/
- Resubmit sitemap.xml in Google Search Console
- Use URL Inspection for the product hub and highest-priority product pages
