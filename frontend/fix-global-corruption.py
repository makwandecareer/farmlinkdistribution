from pathlib import Path
import re
import shutil
import subprocess
from datetime import datetime

ROOT = Path(r"E:\farmlink-production")
FRONTEND = ROOT / "frontend"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")

if not FRONTEND.exists():
    raise SystemExit(f"Frontend folder not found: {FRONTEND}")

MOJIBAKE = {
    "â—": "●", "â—«": "◫", "â™™": "♙", "â–£": "▣",
    "â—Ž": "◎", "â—‡": "◇", "â–¤": "▤", "â‡„": "⇄",
    "âœ“": "✓", "â—‰": "◉", "âœ‰": "✉", "â–±": "▱",
    "â™š": "♚", "â†º": "↺", "â†ª": "↪", "â˜°": "☰",
    "âŒ•": "⌕", "â—": "◐", "â™¢": "♢", "âŒ„": "⌄",
    "Ã—": "×", "Â·": "·", "â€”": "—", "â€“": "–",
    "â€œ": "“", "â€": "”", "â€˜": "‘", "â€™": "’",
    "â€¦": "…", "â†—": "↗", "â‹®": "⋮",
    "Â©": "©", "Â®": "®",
}

extensions = {".html", ".js", ".css", ".txt", ".xml", ".json"}
changed = []
backups = []

for path in FRONTEND.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in extensions:
        continue
    try:
        original = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        continue
    updated = original
    for bad, good in MOJIBAKE.items():
        updated = updated.replace(bad, good)
    updated = updated.replace("\ufeff", "")
    if updated != original:
        backup = path.with_name(path.name + f".global-corruption-fix-{STAMP}.bak")
        shutil.copy2(path, backup)
        backups.append((path, backup))
        path.write_text(updated, encoding="utf-8")
        changed.append(path)

for html_path in FRONTEND.rglob("*.html"):
    text = html_path.read_text(encoding="utf-8-sig")
    updated = re.sub(
        r'((?:src|href)=["\'][^"\']+\.(?:js|css))(?:\?v=[^"\']+)?(["\'])',
        r'\1?v=corruption-fix-1\2',
        text,
    )
    if updated != text:
        if html_path not in changed:
            backup = html_path.with_name(html_path.name + f".global-corruption-fix-{STAMP}.bak")
            shutil.copy2(html_path, backup)
            backups.append((html_path, backup))
            changed.append(html_path)
        html_path.write_text(updated, encoding="utf-8")

failures = []
for path in changed:
    if path.suffix.lower() == ".js":
        result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if result.returncode != 0:
            failures.append((path, result.stderr))

if failures:
    for original, backup in backups:
        shutil.copy2(backup, original)
    raise SystemExit("JavaScript validation failed and changes were rolled back.")

remaining = {}
for path in FRONTEND.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in extensions:
        continue
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        continue
    hits = [token for token in ("â", "Ã", "Â", "ðŸ") if token in text]
    if hits:
        remaining[str(path.relative_to(ROOT))] = hits

print("")
print("FarmLink global corruption repair completed.")
print(f"Files changed: {len(changed)}")
for path in changed:
    print(f"  {path.relative_to(ROOT)}")
print("")
print("JavaScript validation: PASS")
print("Remaining suspicious prefixes:", remaining or "none")
print("")
print(r"git add frontend")
print('git commit -m "Fix corrupted text and icons across FarmLink frontend"')
print(r"git push origin main")
