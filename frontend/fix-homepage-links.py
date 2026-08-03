from pathlib import Path
import shutil
import subprocess
from datetime import datetime

ROOT = Path(r"E:\farmlink-production")
FRONTEND = ROOT / "frontend"
TARGETS = [
    FRONTEND / "index.html",
    FRONTEND / "script.js",
]
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")

REPLACEMENTS = {
    "â†’": "→",
    "â†’": "→",
    "âžœ": "→",
    "âž”": "→",
    "â€”": "—",
    "â€“": "–",
    "â€™": "’",
    "â€œ": "“",
    "â€": "”",
    "Â·": "·",
    "Â©": "©",
    "Ã—": "×",
}

changed = []

for path in TARGETS:
    if not path.exists():
        continue

    original = path.read_text(encoding="utf-8-sig")
    updated = original

    for bad, good in REPLACEMENTS.items():
        updated = updated.replace(bad, good)

    # Remove stray byte-order marks.
    updated = updated.replace("\ufeff", "")

    if updated != original:
        backup = path.with_name(path.name + f".homepage-fix-{STAMP}.bak")
        shutil.copy2(path, backup)
        path.write_text(updated, encoding="utf-8")
        changed.append(path)

# Cache-bust the homepage script so the corrected file loads immediately.
index_path = FRONTEND / "index.html"
if index_path.exists():
    text = index_path.read_text(encoding="utf-8-sig")
    updated = text.replace('src="/script.js"', 'src="/script.js?v=homepage-fix-1"')
    updated = updated.replace('src="/script.js?v=corruption-fix-1"', 'src="/script.js?v=homepage-fix-1"')
    if updated != text:
        if index_path not in changed:
            backup = index_path.with_name(index_path.name + f".homepage-fix-{STAMP}.bak")
            shutil.copy2(index_path, backup)
            changed.append(index_path)
        index_path.write_text(updated, encoding="utf-8")

# Validate JavaScript.
script_path = FRONTEND / "script.js"
if script_path.exists():
    result = subprocess.run(
        ["node", "--check", str(script_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit("JavaScript validation failed:\n" + result.stderr)

# Final scan for common corruption markers in the homepage files.
remaining = {}
for path in TARGETS:
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8-sig")
    hits = [token for token in ("â", "Ã", "Â", "ðŸ") if token in text]
    if hits:
        remaining[str(path.relative_to(ROOT))] = hits

print("")
print("FarmLink homepage link encoding fix completed.")
print("Changed files:")
for path in changed:
    print(f"  {path.relative_to(ROOT)}")
print("")
print("JavaScript validation: PASS")
print("Remaining suspicious prefixes:", remaining or "none")
print("")
print("Next commands:")
print(r"cd /d E:\farmlink-production")
print(r"git status")
print(r"git add frontend\index.html frontend\script.js")
print('git commit -m "Fix homepage service link encoding"')
print(r"git push origin main")
