"""Check alembic heads and migration tree."""
import re
import os

versions_dir = "alembic/versions"
for f in sorted(os.listdir(versions_dir)):
    if not f.endswith(".py") or f == "__init__.py":
        continue
    path = os.path.join(versions_dir, f)
    content = open(path, encoding="utf-8").read()
    rev_match = re.search(r'revision\s*=\s*["\']([^"\']+)["\']', content)
    down_match = re.search(r'down_revision\s*=\s*["\']([^"\']+)["\']', content)
    rev = rev_match.group(1) if rev_match else "?"
    down = down_match.group(1) if down_match else "?"
    print(f"{f}: rev={rev}, down={down}")
