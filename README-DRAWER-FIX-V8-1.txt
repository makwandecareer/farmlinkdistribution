FarmLink Administrator Drawer Fix V8.1

Root cause:
openAdminActions() passed HTML into openDrawer(content), but openDrawer was
defined without a content parameter. The drawer opened while drawerBody stayed
empty, producing a blank white panel with no console error.

Fix:
- openDrawer now accepts and renders optional HTML content.
- Drawer content is cleared after closing.
- Loading states are shown while administrator data is fetched.
- Cache version updated to 8.1.
