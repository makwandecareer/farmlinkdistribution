from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path(r"E:\farmlink-production")
FRONTEND = ROOT / "frontend"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")

if not FRONTEND.exists():
    raise SystemExit(f"Frontend folder not found: {FRONTEND}")

candidates = [
    FRONTEND / "assets" / "farmlink-logo.png",
    FRONTEND / "assets" / "logo.png",
    FRONTEND / "farmlink-logo.png",
    FRONTEND / "logo.png",
]

logo = next((p for p in candidates if p.exists()), None)
if not logo:
    raise SystemExit("FarmLink logo not found in frontend/assets or frontend root.")

favicon_png = FRONTEND / "favicon.png"
apple_icon = FRONTEND / "apple-touch-icon.png"

optimized = False
try:
    from PIL import Image
    image = Image.open(logo).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox:
        image = image.crop(bbox)
    side = max(image.size)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    canvas.alpha_composite(image, ((side-image.width)//2, (side-image.height)//2))
    canvas.resize((512,512), Image.Resampling.LANCZOS).save(favicon_png, "PNG")
    canvas.resize((180,180), Image.Resampling.LANCZOS).save(apple_icon, "PNG")
    optimized = True
except Exception:
    shutil.copy2(logo, favicon_png)
    shutil.copy2(logo, apple_icon)

links = (
    '  <link rel="icon" type="image/png" href="/favicon.png?v=2">\n'
    '  <link rel="shortcut icon" href="/favicon.png?v=2">\n'
    '  <link rel="apple-touch-icon" href="/apple-touch-icon.png?v=2">\n'
)

changed = []
for html_path in FRONTEND.rglob("*.html"):
    text = html_path.read_text(encoding="utf-8-sig")
    updated = re.sub(
        r'\s*<link[^>]+rel=["\'](?:shortcut icon|icon|apple-touch-icon)["\'][^>]*>\s*',
        '\n',
        text,
        flags=re.IGNORECASE,
    )
    if re.search(r'</head>', updated, re.IGNORECASE):
        updated = re.sub(r'</head>', links + '</head>', updated, count=1, flags=re.IGNORECASE)
    if updated != text:
        backup = html_path.with_name(html_path.name + f".favicon-fix-{STAMP}.bak")
        shutil.copy2(html_path, backup)
        html_path.write_text(updated, encoding="utf-8")
        changed.append(html_path.relative_to(ROOT))

print("")
print("FarmLink favicon fix completed.")
print("Source logo:", logo.relative_to(ROOT))
print("Optimized:", "YES" if optimized else "NO - copied original PNG")
print("Pages updated:", len(changed))
print("")
print(r"git add frontend")
print('git commit -m "Add FarmLink favicon across website"')
print(r"git push origin main")
