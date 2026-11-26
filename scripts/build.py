"""Builds armsempiregame.com in place: fills the marked blocks in public/*.html.

Run it from anywhere: python scripts/build.py
Running it twice changes nothing the second time.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aebuild import gallery, links, pages
from aebuild.common import PUBLIC, ROOT, BuildError, has_block, replace_block, write_if_changed


def build():
    site_links = links.load()
    blocks = {}
    blocks.update(gallery.blocks(gallery.collect()))

    changed = []
    for path in sorted(PUBLIC.rglob("*.html")):
        page = path.read_text(encoding="utf-8")
        page = pages.apply_partials(page)
        for name, content in blocks.items():
            if has_block(page, name):
                page = replace_block(page, name, content)
        page = links.apply(page, site_links)
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
