FarmLink Homepage Link Encoding Fix

This fixes corrupted arrow text such as:
Register as a farmer â†’
Register a business â†’
Request an order â†’
View our operating model â†’

Run:
1. Extract this ZIP.
2. Copy the extracted files into E:\farmlink-production
3. Double-click RUN-HOMEPAGE-FIX.cmd

Then:
git status
git add frontend\index.html frontend\script.js
git commit -m "Fix homepage service link encoding"
git push origin main

After deployment press Ctrl+F5.
