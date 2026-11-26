"""Shared parts of every page: icons, navigation, footer, year, asset versions."""

import re

from .common import PUBLIC, file_hash, partial, replace_block, today

VERSIONED = ["assets/css/style.css", "assets/js/main.js"]


def apply_partials(page):
    for name in ("sprite", "nav", "footer"):
        page = replace_block(page, name, partial(name))
    return page


def apply_year(page):
    year = str(today().year)
    return re.sub(r'(<span data-k="year">)[^<]*(</span>)', lambda m: m.group(1) + year + m.group(2), page)


def apply_versions(page):
    """Browsers keep CSS and JS cached, so the URL changes whenever the file does."""
    for rel in VERSIONED:
        path = PUBLIC / rel
        if not path.exists():
            continue
        version = file_hash(path)
        page = re.sub(r'(["\'])/' + re.escape(rel) + r'(?:\?v=[0-9a-f]*)?\1', lambda m: f'{m.group(1)}/{rel}?v={version}{m.group(1)}', page)
    return page


def finish(page):
    return apply_versions(apply_year(page))
