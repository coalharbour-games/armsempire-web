"""Builds armsempiregame.com in place: fills the marked blocks in public/*.html.

Run it from anywhere: python scripts/build.py
Running it twice changes nothing the second time.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aebuild import pages
from aebuild.common import PUBLIC, ROOT, BuildError, write_if_changed


def build():
    changed = []
    for path in sorted(PUBLIC.rglob("*.html")):
        page = path.read_text(encoding="utf-8")
        page = pages.apply_partials(page)
        page = pages.finish(page)
        if write_if_changed(path, page):
            changed.append(path.relative_to(ROOT).as_posix())
    return changed


def main():
    try:
        changed = build()
    except BuildError as e:
        print(f"BUILD FAILED: {e}", file=sys.stderr)
        return 1
    print("Updated: " + ", ".join(changed) if changed else "Nothing to update.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
