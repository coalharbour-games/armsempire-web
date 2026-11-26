"""Screenshot gallery from screenshots/.

A file named 05-tank-factory.jpg becomes screenshot E, "Tank factory": the number
sets the order, the rest of the name is the caption. Files starting with _ are skipped.
"""

import re

from .common import PUBLIC, ROOT, BuildError, esc

SOURCE = ROOT / "screenshots"
OUTPUT = PUBLIC / "media" / "gallery"
URL = "/media/gallery"
HOME_COUNT = 6
SIZES = {"full": 1920, "thumb": 640}
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
NAME = re.compile(r"^(?:(\d+)[-_ ]+)?(.+)$")


def _letter(index):
    letters = ""
    index += 1
    while index:
        index, rest = divmod(index - 1, 26)
        letters = chr(65 + rest) + letters
    return letters


def _caption(slug):
    text = re.sub(r"[-_]+", " ", slug).strip()
    return text[:1].upper() + text[1:]


def _slug(stem):
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def _render(src, dst, width):
    from PIL import Image, ImageOps

    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            if im.width > width:
                im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
            im.save(dst, "JPEG", quality=82, optimize=True, progressive=True)
    except OSError as e:
        raise BuildError(f"screenshots/{src.name}: cannot read the image ({e})")


def collect():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    files = []
    for src in SOURCE.iterdir() if SOURCE.exists() else []:
        if src.name.startswith(("_", ".")) or src.suffix.lower() not in EXTENSIONS:
            continue
        m = NAME.match(src.stem)
        order = int(m.group(1)) if m.group(1) else 10**9
        files.append((order, src.stem.lower(), src, m.group(2)))
    files.sort(key=lambda f: (f[0], f[1]))

    shots, keep = [], set()
    for i, (_, _, src, name) in enumerate(files):
        slug = _slug(src.stem)
        urls = {}
        for size, width in SIZES.items():
            dst = OUTPUT / f"{slug}-{width}.jpg"
            _render(src, dst, width)
            keep.add(dst.name)
            urls[size] = f"{URL}/{dst.name}"
        shots.append({"letter": _letter(i), "caption": _caption(name), **urls})

    for old in OUTPUT.iterdir():
        if old.name not in keep:
            old.unlink()
    return shots


def figures(shots):
    return "\n".join(
        f'<figure class="shot"><a href="{s["full"]}" data-lightbox data-caption="{esc(s["letter"])} / {esc(s["caption"])}">'
        f'<img src="{s["thumb"]}" alt="{esc(s["caption"])}" width="640" height="360" loading="lazy"></a>'
        f'<figcaption class="m">{esc(s["letter"])} / {esc(s["caption"])}</figcaption></figure>'
        for s in shots
    )


def blocks(shots):
    more = ""
    if len(shots) > HOME_COUNT:
        more = f'<p class="shots-more"><a class="btn btn--outline btn--sm" href="/gallery/">All screenshots ({len(shots)}) →</a></p>'
    return {
        "gallery-home": figures(shots[:HOME_COUNT]),
        "gallery-more": more,
        "gallery-all": figures(shots),
    }
