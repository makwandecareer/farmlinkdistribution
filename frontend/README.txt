FarmLink Frontend Encoding Cleanup V1

Purpose
-------
Repairs encoding corruption across the entire frontend without changing design,
layout, wording, URLs, forms, business logic, CSS rules or JavaScript behaviour.

It fixes:
- homepage arrows and punctuation
- city page footers
- product pages
- province pages
- marketplace pages
- administration pages
- UTF-8 BOM issues
- Windows-1252/UTF-8 mojibake

Run
---
1. Extract this ZIP into E:\farmlink-production
2. Run RUN-ENCODING-CLEANUP.cmd
3. Confirm JavaScript validation passes
4. Commit only the frontend changes

Commands:
cd /d E:\farmlink-production
git status
git add frontend
git commit -m "Normalize FarmLink frontend encoding"
git push origin main

After Render deploys, test in a private/incognito browser window.

After confirming the website, run CLEANUP-BACKUPS.cmd and commit the deletion
of any tracked temporary files only if Git reports them.
