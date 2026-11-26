"""Shared helpers for the website build."""

import datetime
import hashlib
import html
import json
import re
from pathlib import Path

SITE = "https://armsempiregame.com"
ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "public"
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Bratislava")
except Exception:
    # Without tzdata on the build machine the dates are still right to the day.
    TZ = datetime.timezone(datetime.timedelta(hours=1))


class BuildError(Exception):
    pass


def today():
    return datetime.datetime.now(TZ).date()


def esc(text):
    return html.escape(str(text), quote=True)


def read_json(name):
    path = DATA / name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise BuildError(f"{path.relative_to(ROOT)}: invalid JSON on line {e.lineno}, column {e.colno}: {e.msg}")
    data.pop("_guide", None)
    return data


def parse_date(value, where):
    try:
        return datetime.date.fromisoformat(str(value))
    except ValueError:
        raise BuildError(f"{where}: date '{value}' must be YYYY-MM-DD")


def format_date(d):
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def partial(name):
    return (TEMPLATES / "partials" / f"{name}.html").read_text(encoding="utf-8").rstrip("\n")


def replace_block(page, name, content):
    """Fill <!--@name-->...<!--/@name--> so the result is the same however often it runs."""
    pattern = re.compile(r"(<!--@" + re.escape(name) + r"-->).*?(<!--/@" + re.escape(name) + r"-->)", re.S)
    body = "\n" + content + "\n" if content else "\n"
    return pattern.sub(lambda m: m.group(1) + body + m.group(2), page)


def has_block(page, name):
    return f"<!--@{name}-->" in page


_TAG = re.compile(r"<([a-zA-Z][a-zA-Z0-9]*)((?:\s+[^\s=>/]+(?:=\"[^\"]*\")?)*)\s*(/?)>")
_ATTR = re.compile(r"\s+([^\s=>/]+)(?:=\"([^\"]*)\")?")


def rewrite_tags(page, attr, fn):
    """Call fn(attrs) for every start tag carrying attr; fn edits the ordered attribute list in place."""
    def repl(m):
        tag, raw, selfclose = m.group(1), m.group(2), m.group(3)
        attrs = [[a.group(1), a.group(2)] for a in _ATTR.finditer(raw)]
        if not any(a[0] == attr for a in attrs):
            return m.group(0)
        fn(attrs)
        out = "".join(f" {k}" if v is None else f' {k}="{v}"' for k, v in attrs)
        return f"<{tag}{out}{' /' if selfclose else ''}>"
    return _TAG.sub(repl, page)


def get_attr(attrs, name):
    for k, v in attrs:
        if k == name:
            return v
    return None


def set_attr(attrs, name, value):
    """value None removes the attribute, True makes it a bare boolean attribute."""
    for i, (k, _) in enumerate(attrs):
        if k == name:
            if value is None:
                del attrs[i]
            else:
                attrs[i][1] = None if value is True else value
            return
    if value is not None:
        attrs.append([name, None if value is True else value])


def file_hash(path):
    return hashlib.sha1(path.read_bytes()).hexdigest()[:8]


def write_if_changed(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.write_text(text, encoding="utf-8")
    return True
