#!/usr/bin/env python3
"""Build index.html from template.html and the Markdown files in content/.

Usage:  python3 build.py

Only uses the Python standard library, so there is nothing to install.
GitHub Actions runs this automatically before every deploy.
"""

import datetime
import html
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

    settings, links = {}, []
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

    if settings.get("interests"):
        items = [i.strip() for i in settings["interests"].split(",") if i.strip()]
        # keep each interest on one line (no breaks at spaces or hyphens)
        safe = [html.escape(i).replace(" ", "&nbsp;").replace("-", "&#8209;") for i in items]
        out.append('<p class="interests"><span>Interests</span> ' + " · ".join(safe) + "</p>")

    link_html = [f"<li>{link_tag(html.escape(label), html.escape(url))}</li>" for label, url in links]
    return settings, out, link_html


# --------------------------------------------------------------------------
# news.md
# --------------------------------------------------------------------------

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
            if kl in ("authors", "venue"):
                fields[kl] = value
            elif kl == "tag":
                tags.append(value)
            elif re.match(r"(https?://|mailto:|assets/|/)", value):
                buttons.append((k[:1].upper() + k[1:], value))
            else:
                warn(f"{path.name}: '{title.strip()}': unknown line: {line}")

        lines = ['<article class="pub">', f"    <h3>{inline(title)}</h3>"]
        if "authors" in fields:
            lines.append(f'    <div class="pub-authors">{inline(fields["authors"])}</div>')
        if "venue" in fields:
            lines.append(f'    <div class="pub-venue">{inline(fields["venue"])}</div>')

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

def main():
    settings, about, links = parse_about(CONTENT / "about.md")
    news = parse_news(CONTENT / "news.md")
    pubs = parse_publications(CONTENT / "publications.md")

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
        "year": str(datetime.date.today().year),
    }
    page = re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), page)
    banner = "<!-- GENERATED by build.py from content/*.md. Edit those files, not this one. -->\n"
    (ROOT / "index.html").write_text(banner + page, encoding="utf-8")

    for w in warnings:
        print("Warning:", w)
    print(f"Built index.html: {len(news) // 4} news items, {len(pubs) and pubs.count('</article>')} publications.")


if __name__ == "__main__":
    main()
