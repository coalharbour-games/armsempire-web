"""Devlog articles from content/devlog/*.md.

Each article becomes public/devlog/<name>/index.html, where <name> is the file
name without .md (and without a leading date, if it has one). Files starting
with _ are templates and are skipped. The header between the --- lines holds:

  title:   required
  date:    required, YYYY-MM-DD
  summary: one or two sentences for the list and for link previews
  image:   cover image, path relative to content/devlog/
  file:    path | description   (an attachment; may repeat)
"""

import re
import shutil

from .common import (
    PUBLIC, ROOT, SITE, TEMPLATES, BuildError, esc, format_date, parse_date, replace_block,
)

SOURCE = ROOT / "content" / "devlog"
OUTPUT = PUBLIC / "devlog"
HOME_COUNT = 3
IMAGE_WIDTH = 1600
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
KNOWN_KEYS = {"title", "date", "summary", "image", "file"}


def _parse(path):
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    where = f"content/devlog/{path.name}"
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        raise BuildError(f"{where}: the file must start with a header between two --- lines")
    meta = {"file": []}
    for n, line in enumerate(m.group(1).split("\n"), 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        key = key.strip().lower()
        if not sep or key not in KNOWN_KEYS:
            raise BuildError(f"{where}, line {n}: expected one of {', '.join(sorted(KNOWN_KEYS))} followed by a colon")
        value = value.strip()
        if key == "file":
            target, _, label = value.partition("|")
            meta["file"].append((target.strip(), label.strip() or target.strip()))
        else:
            meta[key] = value
    for key in ("title", "date"):
        if not meta.get(key):
            raise BuildError(f"{where}: the header needs '{key}:'")
    meta["date"] = parse_date(meta["date"], where)
    meta["body"] = m.group(2)
    meta["where"] = where
    meta["slug"] = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", path.stem).lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", meta["slug"]):
        raise BuildError(f"{where}: use only lowercase letters, digits and dashes in the file name")
    return meta


class _Assets:
    """Copies the files an article uses into its own folder, images scaled down."""

    def __init__(self, article, folder):
        self.article = article
        self.folder = folder
        self.used = {}

    def url(self, ref):
        src = (SOURCE / ref).resolve()
        if SOURCE.resolve() not in src.parents or not src.is_file():
            raise BuildError(f"{self.article['where']}: file '{ref}' not found in content/devlog/")
        name = src.name.lower().replace(" ", "-")
        if self.used.get(name, src) != src:
            raise BuildError(f"{self.article['where']}: two different files are both named '{src.name}'")
        self.used[name] = src
        dst = self.folder / name
        if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
            self.folder.mkdir(parents=True, exist_ok=True)
            if src.suffix.lower() in IMAGE_EXT:
                _scale(src, dst, self.article["where"])
            else:
                shutil.copyfile(src, dst)
        return f"/devlog/{self.article['slug']}/{name}"


def _scale(src, dst, where):
    from PIL import Image, ImageOps

    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            if im.width > IMAGE_WIDTH:
                im = im.resize((IMAGE_WIDTH, round(im.height * IMAGE_WIDTH / im.width)), Image.LANCZOS)
            if dst.suffix.lower() in (".jpg", ".jpeg"):
                im.convert("RGB").save(dst, "JPEG", quality=84, optimize=True, progressive=True)
            else:
                im.save(dst, optimize=True)
    except OSError as e:
        raise BuildError(f"{where}: cannot read image '{src.name}' ({e})")


def _html(article, assets):
    import markdown

    body = re.sub(r"<!--.*?-->", "", article["body"], flags=re.S)
    out = markdown.markdown(body, extensions=["extra", "sane_lists"], output_format="html")

    def local(m):
        attr, ref = m.group(1), m.group(2)
        if re.match(r"^(?:[a-z]+:|/|#)", ref):
            return m.group(0)
        return f'{attr}="{assets.url(ref)}"'

    out = re.sub(r'\b(src|href)="([^"]+)"', local, out)

    def figure(m):
        img = m.group(1)
        title = re.search(r'\stitle="([^"]*)"', img)
        img = re.sub(r'\stitle="[^"]*"', "", img)
        img = img.replace("<img ", '<img loading="lazy" ', 1)
        caption = f"<figcaption>{title.group(1)}</figcaption>" if title else ""
        return f"<figure>{img}{caption}</figure>"

    return re.sub(r"<p>\s*(<img [^>]*>)\s*</p>", figure, out)


def _card(a):
    if a.get("cover"):
        media = f'<div class="crop"><img src="{a["cover"]}" alt="" loading="lazy"></div>'
    else:
        media = '<div class="crop crop--empty" aria-hidden="true"><span class="d">AE</span></div>'
    summary = f"<p>{esc(a['summary'])}</p>" if a.get("summary") else ""
    return (
        f'<a class="post-card" href="/devlog/{a["slug"]}/">{media}<div class="post-card__body">'
        f'<time class="m post-card__date" datetime="{a["date"].isoformat()}">{format_date(a["date"])}</time>'
        f'<h3 class="d">{esc(a["title"])}</h3>{summary}<span class="post-card__more">Read the dispatch →</span></div></a>'
    )


def _page(a, template):
    url = f"{SITE}/devlog/{a['slug']}/"
    image = SITE + a["cover"] if a.get("cover") else f"{SITE}/assets/img/og.jpg"
    description = a.get("summary") or a["title"]
    head = "\n".join([
        f"<title>{esc(a['title'])} — Arms Empire devlog</title>",
        f'<meta name="description" content="{esc(description)}">',
        f'<link rel="canonical" href="{url}">',
        '<meta property="og:type" content="article">',
        '<meta property="og:site_name" content="Arms Empire: Profit of War">',
        f'<meta property="og:title" content="{esc(a["title"])}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{image}">',
        f'<meta property="article:published_time" content="{a["date"].isoformat()}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ])
    cover = f'<figure class="article__cover"><img src="{a["cover"]}" alt=""></figure>' if a.get("cover") else ""
    summary = f'<p class="article__summary">{esc(a["summary"])}</p>' if a.get("summary") else ""
    files = ""
    if a["files"]:
        items = "".join(f'<li><a href="{u}" download>{esc(label)}<span aria-hidden="true">↓</span></a></li>' for u, label in a["files"])
        files = f'<div class="attachments"><div class="m muted">Attachments</div><ul>{items}</ul></div>'
    article = (
        f'<time class="m article__meta" datetime="{a["date"].isoformat()}">Devlog / {format_date(a["date"])}</time>'
        f'\n<h1 class="d">{esc(a["title"])}</h1>\n{summary}\n{cover}\n<div class="prose">\n{a["html"]}\n</div>\n{files}'
        '\n<a class="back-link" href="/devlog/">← All dispatches</a>'
    )
    page = replace_block(template, "head", head)
    return replace_block(page, "article", article)


def build():
    """Returns the article pages to write, the blocks for the other pages and whether any article exists."""
    articles = []
    sources = sorted(SOURCE.glob("*.md")) if SOURCE.exists() else []
    for path in sources:
        if path.name.startswith("_"):
            continue
        articles.append(_parse(path))
    seen = {}
    for a in articles:
        if a["slug"] in seen:
            raise BuildError(f"{a['where']} and {seen[a['slug']]} would have the same address /devlog/{a['slug']}/")
        seen[a["slug"]] = a["where"]
    articles.sort(key=lambda a: (a["date"], a["slug"]), reverse=True)

    template = (TEMPLATES / "article.html").read_text(encoding="utf-8")
    pages = {}
    for a in articles:
        assets = _Assets(a, OUTPUT / a["slug"])
        a["cover"] = assets.url(a["image"]) if a.get("image") else ""
        a["files"] = [(assets.url(ref), label) for ref, label in a["file"]]
        a["html"] = _html(a, assets)
        pages[OUTPUT / a["slug"] / "index.html"] = _page(a, template)
        (OUTPUT / a["slug"]).mkdir(parents=True, exist_ok=True)
        for old in (OUTPUT / a["slug"]).iterdir():
            if old.name != "index.html" and old.name not in assets.used:
                old.unlink()

    for folder in OUTPUT.iterdir():
        if folder.is_dir() and folder.name not in seen:
            shutil.rmtree(folder)

    empty = '<p class="empty">No dispatches yet. The Discord hears it first.</p>'
    blocks = {
        "devlog-home": "\n".join(_card(a) for a in articles[:HOME_COUNT]),
        "devlog-list": "\n".join(_card(a) for a in articles) if articles else empty,
    }
    return pages, blocks, bool(articles)
