# armsempiregame.com

The website of **Arms Empire: Profit of War**. Plain HTML, CSS and JavaScript,
no framework. A small Python build fills in the parts that change (links,
screenshots, devlog, announcements), and Cloudflare serves the result.

- **Desktop only for now.** The layout follows the designer's 1440 px artboard; the
  mobile layout is still to come from the designer.
- **No cookies, no analytics, nothing loaded from other servers.** Keep it that way,
  or update `public/privacy/index.html` first.

## What to change where

| I want to… | Edit | Notes |
|---|---|---|
| add the Steam page, trailer, press kit, contact or studio link | `data/links.json` | An empty `""` hides everything that needs the link; fill it in and it appears. |
| change the social networks | `data/links.json`, `socials` | Shown in this order under "Follow the company". |
| turn on the Share button | `data/links.json`, `share_text` | The message; the link to the site is added after it. |
| add a screenshot | drop it into `screenshots/` | Name it `05-tank-factory.jpg`: the number sets the order, the rest becomes the caption "Tank factory". Files starting with `_` are skipped. The homepage shows the first six. |
| write a devlog article | copy `content/devlog/_template.md` | See [Devlog](#devlog). |
| show an announcement pop-up | `data/overlay.json` | Instructions are inside the file. Images go to `public/assets/img/overlay/`. |
| change a text on the homepage | `public/index.html` | Never edit between `<!--@name-->` and `<!--/@name-->`: the build overwrites it. |
| change the menu or the footer | `templates/partials/nav.html`, `footer.html` | Used on every page. |
| change colours or fonts | `public/assets/css/style.css` | The accent colour is `--accent` at the top. |

Every JSON file in `data/` has a `_guide` with the rules. Keep the quotes and commas
exactly as they are; if the build fails, its message names the file and line.

## Devlog

1. Copy `content/devlog/_template.md` and give the copy a name in lowercase with
   dashes, e.g. `steam-page-is-live.md`. The article will be at
   `armsempiregame.com/devlog/steam-page-is-live/`.
2. Fill in the header between the `---` lines: `title`, `date` (YYYY-MM-DD) and
   ideally `summary` and `image`. Pictures go to `content/devlog/images/`, other
   files to `content/devlog/files/`.
3. Write the text below in Markdown. A picture alone on its own line with a title,
   `![what it shows](images/x.jpg "Caption")`, gets that caption.
4. Push. The newest three articles appear on the homepage; the Devlog section and
   menu item appear with the first article.

To remove an article, delete its `.md` file; its page disappears on the next build.

## Preview on your computer

You need Python 3.11 or newer.

```
pip install -r scripts/requirements.txt
python scripts/build.py
python -m http.server 8000 -d public
```

Open http://localhost:8000. After changing anything, run `python scripts/build.py`
again and reload. Running the build twice changes nothing the second time.

## How it gets online

Every push to `main` makes Cloudflare (Workers Builds) run the build and publish
`public/` as the Worker **armsempire-web** (`wrangler.jsonc`). Pushes to other
branches build a preview, listed under the Worker's **Previews**.

Generated files are not in git: `public/media/` (scaled screenshots) and
`public/devlog/<article>/`. The HTML files the build edits are committed, so the
repository always shows the current site.

### One-time Cloudflare setup

1. Cloudflare dashboard → **Workers & Pages** → open the Worker that should serve
   the site. Its name must be exactly the `name` in `wrangler.jsonc`
   (`armsempire-web`); otherwise the build fails. Either name the Worker so, or
   change `wrangler.jsonc`.
2. **Settings → Builds → Connect**, choose GitHub and the repository
   `coalharbour-games/armsempire-web`, branch `main`.
3. Build settings:
   - Build command: `pip install -r scripts/requirements.txt && python scripts/build.py`
   - Deploy command: `npx wrangler deploy`
   - Root directory: `/`
4. **Settings → Domains & Routes**: add `armsempiregame.com` as a custom domain. If
   another Worker still holds the domain, remove it there first.
5. Push a commit and watch it under **Deployments**.

Cloudflare's Bot Fight Mode and similar features can set their own cookies. Leave
them off, or the privacy page is no longer accurate.

## When something goes wrong

- **The build failed on Cloudflare.** Open the failed deployment's log; the line
  starting with `BUILD FAILED:` says which file and what is wrong. Fix it and push
  again. The site stays on the last good version in the meantime.
- **My change is not visible.** Wait a minute, then reload with Ctrl+F5. CSS and JS
  carry a version in their address, so an old copy cannot stick.
- **An image is missing.** File names are case-sensitive online: `Tank.JPG` and
  `tank.jpg` are different files.

## Structure

```
public/                the website (Cloudflare serves this folder)
  index.html           homepage
  gallery/  devlog/  privacy/  404.html
  assets/              css, js, fonts (OFL, see fonts/README.txt), images
content/devlog/        devlog articles in Markdown
screenshots/           source images of the gallery
data/                  links.json, overlay.json
templates/             menu, footer and icons shared by all pages; article page
scripts/build.py       the build; its parts are in scripts/aebuild/
wrangler.jsonc         Cloudflare Worker settings
```
