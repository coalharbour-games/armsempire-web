"""Links from data/links.json: fills hrefs and hides whatever needs a missing link.

In the HTML:
  data-link="steam"           the build sets href to that link
  data-link="social:YouTube"  the build sets href to that entry of "socials"
  data-needs="steam"          hidden while the link is empty
  data-needs="!steam"         hidden once the link is filled in
  data-needs="steam trailer"  hidden unless all of them hold
  data-share                  the build puts share_text into its data-text
"""

from .common import BuildError, esc, get_attr, read_json, replace_block, rewrite_tags, set_attr

SINGLE = ("discord", "steam", "trailer", "press_kit", "press_key", "contact", "studio")
TEXTS = ("share_text",)


def load():
    links = read_json("links.json")
    for key in SINGLE:
        value = links.get(key)
        if not isinstance(value, str):
            raise BuildError(f'data/links.json: "{key}" must be text, use "" when there is no link')
        _check_url(key, value)
    for key in TEXTS:
        if not isinstance(links.get(key), str):
            raise BuildError(f'data/links.json: "{key}" must be text, use "" when there is none')
    socials = links.get("socials")
    if not isinstance(socials, list):
        raise BuildError('data/links.json: "socials" must be a list')
    for i, s in enumerate(socials, 1):
        if not isinstance(s, dict) or not s.get("name") or not s.get("url"):
            raise BuildError(f'data/links.json: socials item {i} needs both "name" and "url"')
        _check_url(f"socials item {i}", s["url"])
    return links


def _check_url(key, value):
    if value and not value.startswith(("https://", "mailto:")):
        raise BuildError(f'data/links.json: "{key}" must start with https:// or mailto:, got "{value}"')


def _resolve(links, key):
    if key.startswith("social:"):
        name = key[len("social:"):]
        for s in links["socials"]:
            if s["name"] == name:
                return s["url"]
        return ""
    if key not in links or key == "socials":
        raise BuildError(f'the page asks for link "{key}", which data/links.json does not have')
    return links[key]


def _flag_holds(links, flags, extra):
    for flag in flags.split():
        negate = flag.startswith("!")
        name = flag.lstrip("!")
        value = extra[name] if name in extra else bool(_resolve(links, name))
        if value == negate:
            return False
    return True


def apply(page, links, extra=None):
    """extra: further flags a page can test with data-needs, e.g. {"devlog": True}."""
    extra = extra or {}

    def fill(attrs):
        url = _resolve(links, get_attr(attrs, "data-link"))
        set_attr(attrs, "href", esc(url) if url else "#")

    def toggle(attrs):
        set_attr(attrs, "hidden", None if _flag_holds(links, get_attr(attrs, "data-needs"), extra) else True)

    def share(attrs):
        set_attr(attrs, "data-text", esc(links["share_text"]))

    page = rewrite_tags(page, "data-link", fill)
    page = rewrite_tags(page, "data-share", share)
    page = rewrite_tags(page, "data-needs", toggle)
    if "<!--@socials-->" in page:
        items = "\n".join(
            f'<a href="{esc(s["url"])}">{esc(s["name"])}<span aria-hidden="true">↗</span></a>' for s in links["socials"]
        )
        page = replace_block(page, "socials", items)
    return page
