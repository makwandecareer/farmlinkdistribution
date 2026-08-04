from pathlib import Path
import shutil
import subprocess
from datetime import datetime

ROOT = Path(r"E:\farmlink-production")
FRONTEND = ROOT / "frontend"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")

if not FRONTEND.exists():
    raise SystemExit(f"Frontend directory not found: {FRONTEND}")

EXTENSIONS = {".html", ".js", ".css", ".json", ".xml", ".txt"}

# Explicit replacements for all encoding artefacts observed in FarmLink.
REPLACEMENTS = {
    "┬⌐": "©",
    "┬╖": "•",
    "â€¢": "•",
    "â†’": "→",
    "â†’": "→",
    "â€”": "—",
    "â€“": "–",
    "â€¦": "…",
    "â€™": "’",
    "â€˜": "‘",
    "â€œ": "“",
    "â€": "”",
    "â„¢": "™",
    "âœ“": "✓",
    "âœ”": "✔",
    "âœ•": "✕",
    "âœ‰": "✉",
    "â˜°": "☰",
    "â—": "●",
    "â—‹": "○",
    "â—‡": "◇",
    "â—‰": "◉",
    "â—": "◐",
    "â™™": "♙",
    "â™š": "♚",
    "â™¢": "♢",
    "â–£": "▣",
    "â–¤": "▤",
    "â–±": "▱",
    "â‡„": "⇄",
    "â†º": "↺",
    "â†ª": "↪",
    "â†—": "↗",
    "âŒ•": "⌕",
    "âŒ„": "⌄",
    "â‹®": "⋮",
    "Ã—": "×",
    "Ã©": "é",
    "Ã¨": "è",
    "Ãª": "ê",
    "Ã¡": "á",
    "Ã³": "ó",
    "Ã¶": "ö",
    "Ã¼": "ü",
    "Â©": "©",
    "Â®": "®",
    "Â·": "·",
    "Â ": " ",
}

SUSPICIOUS = ("â", "Ã", "Â", "ðŸ", "┬", "╖", "⌐")

changed = []
backups = []

for path in FRONTEND.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
        continue

    raw = path.read_bytes()

    # Prefer UTF-8 with BOM handling. Fall back to Windows-1252 only when needed.
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")

    original = text

    for bad, good in REPLACEMENTS.items():
        text = text.replace(bad, good)

    text = text.replace("\ufeff", "")

    if text != original or raw.startswith(b"\xef\xbb\xbf"):
        backup = path.with_name(path.name + f".encoding-cleanup-{STAMP}.bak")
        shutil.copy2(path, backup)
        backups.append((path, backup))
        path.write_text(text, encoding="utf-8", newline="\n")
        changed.append(path)

# Validate changed JavaScript files.
failures = []
for path in changed:
    if path.suffix.lower() == ".js":
        result = subprocess.run(
            ["node", "--check", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append((path, result.stderr))

if failures:
    for original, backup in backups:
        shutil.copy2(backup, original)
    details = "\n\n".join(f"{p}\n{err}" for p, err in failures)
    raise SystemExit("JavaScript validation failed. All modified files were restored.\n" + details)

# Final scan.
remaining = {}
for path in FRONTEND.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
        continue
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        continue
    hits = [token for token in SUSPICIOUS if token in text]
    if hits:
        remaining[str(path.relative_to(ROOT))] = hits

print("")
print("FarmLink frontend encoding cleanup completed.")
print(f"Files changed: {len(changed)}")
for path in changed:
    print(f"  {path.relative_to(ROOT)}")
print("")
print("JavaScript validation: PASS")
print("Remaining suspicious sequences:", remaining or "none")
print("")
print("Next commands:")
print(r"cd /d E:\farmlink-production")
print(r"git status")
print(r"git add frontend")
print('git commit -m "Normalize FarmLink frontend encoding"')
print(r"git push origin main")
