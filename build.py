#!/usr/bin/env python3
"""Build index.html from template.html and the Markdown files in content/.

Usage:  python3 build.py

Only uses the Python standard library, so there is nothing to install.
GitHub Actions runs this automatically before every deploy.
"""

import datetime
import html
import json
import struct
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"

warnings = []


def warn(msg):
    warnings.append(msg)


# --------------------------------------------------------------------------
# Tiny Markdown helpers (only what this site needs: links, bold, italic)
# --------------------------------------------------------------------------

def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def link_tag(label, url):
    external = url.startswith("http://") or url.startswith("https://")
    extra = ' target="_blank" rel="noopener"' if external else ""
    return f'<a href="{url}"{extra}>{label}</a>'


def inline(text):
    """Convert inline Markdown to HTML. The text is HTML-escaped first."""
    s = html.escape(text.strip(), quote=True)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: link_tag(m.group(1), m.group(2)), s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", s)
    return s


def indent(lines, n):
    pad = " " * n
    return "\n".join(pad + line if line else line for line in lines)


# --------------------------------------------------------------------------
# about.md
# --------------------------------------------------------------------------

def parse_about(path):
    raw = strip_comments(path.read_text(encoding="utf-8"))
    m = re.match(r"\s*---\s*\n(.*?)\n---\s*\n(.*)", raw, flags=re.S)
    if not m:
        sys.exit(f"{path.name}: missing the settings block between two --- lines at the top")
    settings_text, body = m.groups()

    settings, links, skill_rows, highlights = {}, [], [], []
    for line in settings_text.splitlines():
        line = line.strip()
        if not line:
            continue
        key, sep, value = line.partition(":")
        if not sep:
            warn(f"{path.name}: ignored settings line (no colon): {line}")
            continue
        key, value = key.strip().lower(), value.strip()
        if key == "link":
            label, bar, url = value.partition("|")
            if not bar:
                warn(f"{path.name}: link needs 'Label | url': {line}")
                continue
            links.append((label.strip(), url.strip()))
        elif key == "highlight":
            label, _, url = value.partition("|")
            highlights.append((label.strip(), url.strip()))
        elif key == "skill":
            group, bar, items = value.partition("|")
            if not bar:
                warn(f"{path.name}: skill needs 'Group | item, item': {line}")
                continue
            skill_rows.append((group.strip(), [i.strip() for i in items.split(",") if i.strip()]))
        else:
            settings[key] = value

    for required in ("name", "role", "photo"):
        if required not in settings:
            sys.exit(f"{path.name}: missing '{required}:' in the settings block")

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    out, lead_done = [], False
    for p in paragraphs:
        if p.startswith(">"):
            text = " ".join(line.lstrip(">").strip() for line in p.splitlines())
            out.append(f'<p class="open-to">{inline(text)}</p>')
        else:
            text = " ".join(line.strip() for line in p.splitlines())
            cls = "" if lead_done else ' class="lead"'
            lead_done = True
            out.append(f"<p{cls}>{inline(text)}</p>")

    # "Skills & Service" rows, shown at the bottom of the page
    def nobreak(item):  # keep each skill on one line (no breaks at spaces or hyphens)
        return html.escape(item).replace(" ", "&nbsp;").replace("-", "&#8209;")

    rows = []
    for group, items in skill_rows:
        if items:
            rows += ["    <div>", f"        <dt>{html.escape(group)}</dt>",
                     f"        <dd>{', '.join(nobreak(i) for i in items)}</dd>", "    </div>"]
    if settings.get("service", "").strip():
        rows += ["    <div>", "        <dt>Service</dt>",
                 f"        <dd>{inline(settings['service'])}</dd>", "    </div>"]
    settings["_skills"] = [i for _, items in skill_rows for i in items]
    settings["_meta"] = ['<dl class="meta-list">'] + rows + ["</dl>"] if rows else []

    settings["_links"] = links
    settings["_highlights"] = []
    if highlights:
        items = []
        for label, url in highlights:
            text = inline(label)
            items.append(f"    <li>{link_tag(text, html.escape(url)) if url else text}</li>")
        settings["_highlights"] = ['<ul class="highlights" aria-label="Research highlights">'] + items + ["</ul>"]
    link_html = [f"<li>{link_tag(html.escape(label), html.escape(url))}</li>" for label, url in links]
    return settings, out, link_html


# --------------------------------------------------------------------------
# news.md
# --------------------------------------------------------------------------

def plain(text):
    """Caption text without Markdown, for alt text."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return re.sub(r"\*+", "", text).strip()


def image_ratio(img):
    """Width / height of a JPEG or PNG (standard library only). Falls back to 4:3."""
    path = ROOT / img
    try:
        data = path.read_bytes()
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24])
            return w / h
        i = 2
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                i += 2
                continue
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w / h
            i += 2 + length
    except (OSError, struct.error, ZeroDivisionError):
        pass
    return 4 / 3


def slugify(text, used):
    slug = re.sub(r"[^a-z0-9]+", "-", plain(text).lower()).strip("-") or "event"
    base, n = slug, 2
    while slug in used:
        slug, n = f"{base}-{n}", n + 1
    used.add(slug)
    return slug


def parse_gallery(path):
    """Events from gallery.md: [{title, date, place, slug, photos: [(img, caption)]}]."""
    if not path.exists():
        return []
    raw = strip_comments(path.read_text(encoding="utf-8"))
    events, used = [], set()
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            parts = [x.strip() for x in line[3:].split("|")] + ["", ""]
            title = parts[0] or "Photos"
            events.append({"title": title, "date": parts[1], "place": parts[2],
                           "slug": slugify(title, used), "photos": []})
        elif line.startswith("- "):
            img, _, caption = (x.strip() for x in line[2:].partition("|"))
            if not img:
                warn(f"{path.name}: skipped empty photo line: {line}")
                continue
            if not (ROOT / img).exists() and not img.startswith("http"):
                warn(f"{path.name}: photo not found: {img}")
            if not events:  # photos before any ## line
                events.append({"title": "Photos", "date": "", "place": "",
                               "slug": slugify("Photos", used), "photos": []})
            events[-1]["photos"].append((img, caption.split("|")[0].strip()))
        else:
            warn(f"{path.name}: skipped line (expected '## Event | Mon YYYY | Place' or '- photo.jpg'): {line}")
    return [e for e in events if e["photos"]]


def event_meta(e, with_count=False):
    bits = [e["date"], e["place"]]
    if with_count:
        n = len(e["photos"])
        bits.append(f"{n} photo" + ("" if n == 1 else "s"))
    return " · ".join(html.escape(b) for b in bits if b)


def gallery_home(events):
    """Home page: one cover tile per event, linking to that event on gallery.html."""
    out = []
    for e in events:
        img = html.escape(e["photos"][0][0])
        title = inline(e["title"])
        meta = event_meta(e, with_count=True)
        out += [
            '<figure class="gallery-item">',
            f'    <a class="gallery-open gallery-cover" href="gallery.html#{e["slug"]}">',
            f'        <img src="{img}" alt="{html.escape(plain(e["title"]))}" loading="lazy">',
            "    </a>",
            f'    <figcaption><span class="gallery-date">{meta}</span>{title}</figcaption>',
            "</figure>",
        ]
    return out


def split_date(date):
    """'Jul 2026' -> ('Jul', '2026'); anything else -> (date, '')."""
    m = re.fullmatch(r"([A-Za-z]+)\.?\s+(\d{4})", date.strip())
    return (m.group(1)[:3].title(), m.group(2)) if m else (date.strip(), "")


def gallery_page_html(events):
    """Gallery page: filter buttons (All + one per event), then one collage of every
    photo. Each photo knows its event, so a filter shows just that event."""
    total = sum(len(e["photos"]) for e in events)
    out = ['<div class="gallery-filters" role="group" aria-label="Show photos from">',
           f'    <button type="button" data-filter="all" aria-pressed="true">All photos <span>{total}</span></button>']
    out += [f'    <button type="button" data-filter="{e["slug"]}" aria-pressed="false">{inline(e["title"])} <span>{len(e["photos"])}</span></button>'
            for e in events]
    out += ["</div>", "", '<div class="gallery-grid is-collage">']
    for e in events:
        meta = event_meta(e)  # date · place
        for img, caption in e["photos"]:
            alt = html.escape(plain(caption or e["title"]))
            text = inline(e["title"]) + (f'<span class="gallery-caption">{inline(caption)}</span>' if caption else "")
            date_html = f'<span class="gallery-date">{meta}</span>' if meta else ""
            out += [
                f'    <figure class="gallery-item" data-event="{e["slug"]}">',
                f'        <button type="button" class="gallery-open" data-full="{html.escape(img)}" aria-label="Enlarge photo: {alt}">',
                f'            <img src="{html.escape(img)}" alt="{alt}" loading="lazy">',
                "        </button>",
                f"        <figcaption>{date_html}{text}</figcaption>",
                "    </figure>",
            ]
    out.append("</div>")
    return out


def parse_news(path):
    raw = strip_comments(path.read_text(encoding="utf-8"))
    items = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if not line.startswith("- ") or "|" not in line:
            warn(f"{path.name}: skipped line (expected '- Mon YYYY | text'): {line}")
            continue
        date, _, text = line[2:].partition("|")
        items += [
            '<li class="news-item">',
            f'    <span class="news-date">{html.escape(date.strip())}</span>',
            f'    <span class="news-content">{inline(text)}</span>',
            "</li>",
        ]
    return items


def is_url(value):
    return re.match(r"(https?://|mailto:|assets/|/)", value) is not None


def button_label(key):
    return key[:1].upper() + key[1:]


# --------------------------------------------------------------------------
# projects.md
# --------------------------------------------------------------------------

def parse_projects(path):
    if not path.exists():
        return []
    raw = strip_comments(path.read_text(encoding="utf-8"))
    out = []
    for block in re.split(r"^##\s+", raw, flags=re.M)[1:]:
        title, _, rest = block.partition("\n")
        fields, buttons, tags, text = {}, [], [], []
        for line in rest.splitlines():
            line = line.strip()
            if not line:
                continue
            m = re.match(r"([A-Za-z][\w .-]{0,30}):\s*(.*)$", line)
            key = m.group(1).strip() if m else ""
            value = m.group(2).strip() if m else ""
            if m and key.lower() in ("label", "image", "alt"):
                fields[key.lower()] = value
            elif m and key.lower() == "tag":
                tags.append(value)
            elif m and is_url(value):
                buttons.append((button_label(key), value))
            else:
                text.append(line)

        lines = ['<article class="project">']
        if fields.get("image"):
            alt = html.escape(fields.get("alt", title.strip()))
            lines.append(f'    <img src="{html.escape(fields["image"])}" alt="{alt}" loading="lazy">')
        lines.append('    <div class="project-body">')
        if fields.get("label"):
            lines.append(f'        <div class="project-label">{inline(fields["label"])}</div>')
        lines.append(f"        <h3>{inline(title)}</h3>")
        if text:
            lines.append(f"        <p>{inline(' '.join(text))}</p>")
        if buttons or tags:
            lines.append('        <div class="pub-links">')
            for t in tags:
                lines.append(f'            <span class="pub-tag">{inline(t)}</span>')
            for label, url in buttons:
                lines.append(f"            {link_tag(html.escape(label), html.escape(url))}")
            lines.append("        </div>")
        lines += ["    </div>", "</article>"]
        out += lines
    return out


# --------------------------------------------------------------------------
# publications.md
# --------------------------------------------------------------------------

def parse_publications(path):
    raw = strip_comments(path.read_text(encoding="utf-8"))
    blocks = re.split(r"^##\s+", raw, flags=re.M)[1:]
    out, used_ids = [], set()

    for n, block in enumerate(blocks, 1):
        title, _, rest = block.partition("\n")
        bib = None
        bm = re.search(r"```\s*bibtex\s*\n(.*?)```", rest, flags=re.S)
        if bm:
            bib = bm.group(1).strip("\n")
            rest = rest[: bm.start()] + rest[bm.end():]

        fields, buttons, tags = {}, [], []
        for line in rest.splitlines():
            line = line.strip()
            if not line:
                continue
            key, sep, value = line.partition(":")
            if not sep:
                warn(f"{path.name}: '{title.strip()}': ignored line: {line}")
                continue
            k, value = key.strip(), value.strip()
            kl = k.lower()
            if kl in ("authors", "venue", "tech"):
                fields[kl] = value
            elif kl == "tag":
                tags.append(value)
            elif is_url(value):
                buttons.append((button_label(k), value))
            else:
                warn(f"{path.name}: '{title.strip()}': unknown line: {line}")

        lines = ['<article class="pub">', f"    <h3>{inline(title)}</h3>"]
        if "authors" in fields:
            lines.append(f'    <div class="pub-authors">{inline(fields["authors"])}</div>')
        if "venue" in fields:
            lines.append(f'    <div class="pub-venue">{inline(fields["venue"])}</div>')
        tech = [t.strip() for t in fields.get("tech", "").split(",") if t.strip()]
        if len(tech) > 4:
            warn(f"{path.name}: '{title.strip()}': only the first 4 tech tags are shown")
            tech = tech[:4]
        if tech:
            lines.append('    <ul class="pub-tech" aria-label="Methods and tools">')
            lines += [f"        <li>{inline(t)}</li>" for t in tech]
            lines.append("    </ul>")

        bib_id = None
        if bib:
            km = re.match(r"\s*@\w+\s*\{\s*([^,\s]+)", bib)
            bib_id = re.sub(r"[^\w-]", "", km.group(1)) if km else f"pub{n}"
            while bib_id in used_ids:
                bib_id += "_"
            used_ids.add(bib_id)

        if buttons or bib or tags:
            lines.append('    <div class="pub-links">')
            for label, url in buttons:
                lines.append(f"        {link_tag(html.escape(label), html.escape(url))}")
            if bib_id:
                lines.append(f'        <button type="button" data-bibtex="{bib_id}">BibTeX</button>')
            for t in tags:
                lines.append(f'        <span class="pub-tag">{inline(t)}</span>')
            lines.append("    </div>")

        if bib_id:
            lines.append(f'    <div id="bib_{bib_id}" class="bibtex" hidden>')
            lines.append(f"        <pre>{html.escape(bib)}</pre>")
            lines.append("    </div>")
        lines.append("</article>")
        out += lines + [""]

    return out[:-1] if out else out


# --------------------------------------------------------------------------
# Extra <head> tags: structured data for search engines, optional analytics
# --------------------------------------------------------------------------

SITE_URL = "https://shruti-bt.github.io/"


def head_extra(settings):
    role_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", settings["role"])
    job_title, _, org = role_text.partition(",")
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": settings["name"],
        "url": SITE_URL,
        "image": SITE_URL + settings["photo"],
        "jobTitle": job_title.strip(),
        "sameAs": [url for _, url in settings["_links"] if url.startswith("http")],
    }
    if org.strip():
        person["worksFor"] = {"@type": "Organization", "name": org.strip()}
    if settings["_skills"]:
        person["knowsAbout"] = settings["_skills"]
    data = json.dumps(person, indent=2, ensure_ascii=False).replace("</", "<\\/")
    lines = ['<script type="application/ld+json">'] + data.splitlines() + ["</script>"]

    code = settings.get("analytics", "").strip()
    if code:
        if not re.fullmatch(r"[a-z0-9-]+", code):
            warn(f"about.md: analytics should be just your GoatCounter code, e.g. shruti-bt (got {code!r})")
        else:
            lines.append(f'<script data-goatcounter="https://{code}.goatcounter.com/count" '
                         'async src="https://gc.zgo.at/count.js"></script>')
    return lines


# --------------------------------------------------------------------------

def main():
    settings, about, links = parse_about(CONTENT / "about.md")
    projects = parse_projects(CONTENT / "projects.md")
    events = parse_gallery(CONTENT / "gallery.md")
    photo_count = sum(len(e["photos"]) for e in events)
    gallery = gallery_home(events)
    news = parse_news(CONTENT / "news.md")
    pubs = parse_publications(CONTENT / "publications.md")
    patents = parse_publications(CONTENT / "patents.md") if (CONTENT / "patents.md").exists() else []

    page = (ROOT / "template.html").read_text(encoding="utf-8")
    page = re.sub(r"\n<!--\s*\n\s*This is the page layout.*?-->\n", "\n", page, count=1, flags=re.S)
    values = {
        "name": html.escape(settings["name"]),
        # same name, but a double surname never splits across lines
        "name_nobreak": html.escape(settings["name"]).replace("-", "&#8209;"),
        "role": inline(settings["role"]),
        "photo": html.escape(settings["photo"]),
        "about": indent(about, 16),
        "links": indent(links, 16),
        "news": indent(news, 20),
        "publications": indent(pubs, 12),
        "pub_heading": indent(
            ['<div class="section-tabs" role="tablist" aria-label="Publications and patents">',
             '    <button type="button" role="tab" id="tab-publications" aria-controls="panel-publications" aria-selected="true">Publications</button>',
             '    <button type="button" role="tab" id="tab-patents" aria-controls="panel-patents" aria-selected="false" tabindex="-1">Patents</button>',
             '</div>'] if patents else ["<h2>Publications</h2>"], 12),
        "patents_panel": indent(
            ['<div id="panel-patents" role="tabpanel" aria-labelledby="tab-patents">']
            + ["    " + line if line else line for line in patents] + ["</div>"] if patents else [], 12),
        "projects": indent(projects, 16),
        "gallery": indent(gallery, 16),
        "gallery_more": (f'            <a href="gallery.html" class="gallery-more">See all {photo_count} photos &rarr;</a>'
                         if photo_count else ""),
        "meta": indent(settings["_meta"], 12),
        "highlights": indent(settings["_highlights"], 20),
        "head_extra": indent(head_extra(settings), 4),
        "year": str(datetime.date.today().year),
    }
    if not gallery:  # no photos yet: drop the Gallery section and its nav link
        page = re.sub(r"\n\s*<section id=\"gallery\">.*?</section>\n", "\n", page, flags=re.S)
        page = re.sub(r"\n\s*<dialog class=\"lightbox\".*?</dialog>", "", page, flags=re.S)
        page = re.sub(r"\n\s*<a href=\"#gallery\"[^\n]*", "", page)
    if settings.get("show_projects", "no").strip().lower() not in ("yes", "on", "true"):
        # Selected Work is switched off: drop the section and its nav link
        page = re.sub(r"\n\s*<section id=\"work\">.*?</section>\n", "\n", page, flags=re.S)
        page = re.sub(r"\n\s*<a href=\"#work\"[^\n]*", "", page)
        projects = []
    if not settings["_meta"]:  # no skills or service: drop the whole section
        page = re.sub(r"\n\s*<section id=\"skills\">.*?</section>\n", "\n", page, flags=re.S)
    page = re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), page)
    banner = "<!-- GENERATED by build.py from content/*.md. Edit those files, not this one. -->\n"
    (ROOT / "index.html").write_text(banner + page, encoding="utf-8")

    # The full Gallery page (gallery.html): every photo as a collage
    gallery_page = ROOT / "gallery.html"
    if gallery:
        first_photo = events[0]["photos"][0][0]
        gvalues = dict(values, gallery=indent(gallery_page_html(events), 8), og_image=first_photo)
        gpage = (ROOT / "template-gallery.html").read_text(encoding="utf-8")
        gpage = re.sub(r"\n<!--\s*\n\s*Layout of the Gallery page.*?-->\n", "\n", gpage, count=1, flags=re.S)
        gpage = re.sub(r"\{\{(\w+)\}\}", lambda m: gvalues.get(m.group(1), m.group(0)), gpage)
        gallery_page.write_text(banner.replace("content/*.md", "content/gallery.md") + gpage, encoding="utf-8")
    elif gallery_page.exists():
        gallery_page.unlink()  # no photos: no gallery page

    for w in warnings:
        print("Warning:", w)
    print(f"Built index.html: {projects.count('</article>')} projects shown, {len(news) // 4} news items, "
          f"{pubs.count('</article>')} publications, {patents.count('</article>')} patents, {photo_count} photos in {len(events)} events.")


if __name__ == "__main__":
    main()
