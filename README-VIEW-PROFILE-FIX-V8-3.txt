FarmLink Administrator View Profile Fix V8.3

Root cause:
The profile drawer called detail(...) for each field, but this admin.js build
did not define a detail helper. The exception was caught, so the profile did
not render.

Fix:
- Added profileDetail(label, value).
- Updated the administrator profile renderer to use profileDetail.
- Added explicit console error reporting.
- Cache version updated to 8.3.
