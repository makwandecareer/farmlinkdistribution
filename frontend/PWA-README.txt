FarmLink PWA installation package

Replace:
  frontend/index.html
with:
  index-pwa.html

Add these files to frontend/:
  manifest.json
  service-worker.js
  offline.html
  pwa-install.js

The existing /assets/farmlink-logo.png is used as the initial app icon.
For Google Play publication later, add proper square 192x192 and 512x512 PNG icons.

Windows CMD deployment:
  cd /d E:\farmlink-production
  copy /Y "frontend\index-pwa.html" "frontend\index.html"
  del /Q "frontend\index-pwa.html"
  git add -A
  git commit -m "Convert FarmLink website to installable PWA"
  git push origin main

After deployment:
  Open the site in Chrome on Android.
  Use browser menu > Add to Home screen / Install app.
