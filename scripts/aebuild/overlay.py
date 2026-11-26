"""Homepage announcements from data/overlay.json; the browser decides by date which one to show."""

import json

from .common import PUBLIC, BuildError, parse_date, read_json

REQUIRED = ("id", "from", "to", "title")
OPTIONAL = ("kicker", "text", "image", "image_alt", "button", "link")
IMAGE_LIMIT = 250 * 1024


def build():
    data = read_json("overlay.json")
    items = data.get("items")
    if not isinstance(items, list):
        raise BuildError('data/overlay.json: "items" must be a list')
    out, ids = [], set()
    for n, item in enumerate(items, 1):
        where = f"data/overlay.json, item {n}"
        if not isinstance(item, dict):
            raise BuildError(f"{where}: must be {{ ... }}")
        unknown = set(item) - set(REQUIRED) - set(OPTIONAL)
        if unknown:
            raise BuildError(f"{where}: unknown field(s) {', '.join(sorted(unknown))}")
        for key in REQUIRED:
            if not str(item.get(key, "")).strip():
                raise BuildError(f"{where}: '{key}' is required")
        if item["id"] in ids:
            raise BuildError(f"{where}: id '{item['id']}' is used twice")
        ids.add(item["id"])
        start, end = parse_date(item["from"], where), parse_date(item["to"], where)
        if end < start:
            raise BuildError(f"{where}: 'to' is before 'from'")
        if bool(item.get("button")) != bool(item.get("link")):
            raise BuildError(f"{where}: 'button' and 'link' go together")
        if item.get("link") and not item["link"].startswith(("https://", "/")):
            raise BuildError(f"{where}: 'link' must start with https:// or /")
        if item.get("image"):
            path = PUBLIC / item["image"].lstrip("/")
            if not item["image"].startswith("/") or not path.is_file():
                raise BuildError(f"{where}: image '{item['image']}' not found in public/")
            if path.stat().st_size > IMAGE_LIMIT:
                print(f"WARNING {where}: image has {path.stat().st_size // 1024} KB, keep it under 250 KB")
            if not item.get("image_alt"):
                raise BuildError(f"{where}: 'image_alt' describes the image for people who cannot see it")
        out.append({k: str(item[k]) for k in REQUIRED + OPTIONAL if item.get(k)})
    payload = json.dumps(out, ensure_ascii=False).replace("<", "\\u003c")
    return {"overlay": f'<script type="application/json" id="overlay-data">{payload}</script>'}
