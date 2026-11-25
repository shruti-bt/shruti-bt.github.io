# shruti-bt.github.io

Personal academic website, live at **https://shruti-bt.github.io**.

## How to update the site

All the text lives in Markdown files in `content/`. Edit them, push to `main`, and
GitHub rebuilds and publishes the site automatically.

| To change...                                        | Edit                        |
|-----------------------------------------------------|-----------------------------|
| Name, role, photo, links, highlights, skills, service | `content/about.md` (settings block at the top) |
| Bio paragraphs, "open to roles" box                 | `content/about.md` (below the settings) |
| News & Highlights                                   | `content/news.md`           |
| Papers and posters                                  | `content/publications.md`   |
| Patents (the second tab next to Publications)       | `content/patents.md`        |
| Gallery photos, grouped by event                    | `content/gallery.md` + `assets/img/gallery/` |

Each file starts with a short **HOW TO EDIT** note showing the format.

### Quick examples

Add a news item (top of `content/news.md`, newest first):

```
- Dec 2026 | Started a new role as **Research Engineer** at [Company](https://example.com).
```

Add a paper (`content/publications.md`, newest first):

````
## Paper Title
authors: **Shrutika Thengane**, Co-Author, [Advisor](https://...)
venue: Conference Name, 2026
paper: https://arxiv.org/abs/...
tag: Oral

```bibtex
@inproceedings{key2026,
  ...
}
```
````

Any `label: https://...` line becomes a button (`paper`, `video`, `slides`, ...).
Formatting that works everywhere: `**bold**`, `*italic*`, `[link text](https://...)`.

### Gallery

Copy a photo into `assets/img/gallery/` and add it under its event in `content/gallery.md`:

```
## IEEE MRS 2025 | Dec 2025 | SUTD, Singapore
- assets/img/gallery/mrs-welcome.jpg | The team at MRS 2025
```

The home page shows the first three events. "See all photos" opens the Gallery page
(`gallery/index.html`), with every photo in one collage and a filter per event.
With no photos, the Gallery section, its menu link and the Gallery page all disappear.

**The gallery is currently kept on this computer only** (see `.gitignore`) until the
photos are cleared for sharing. To publish it, remove the gallery lines from `.gitignore`
and commit.

## Previewing on your computer

```
python3 build.py
```

Then open `index.html` in your browser. (`build.py` needs no installs. GitHub runs it on every push, so this step is only
for previewing.)

## Files

```
content/              ← the text (edit these)
templates/home.html   ← home page layout with {{placeholders}}
templates/gallery.html← Gallery page layout
build.py              ← turns content/ + templates/ into the pages below
assets/css/style.css  ← colours, fonts, spacing (theme variables at the top)
assets/js/main.js     ← tabs, BibTeX, sticky menu, dark mode, gallery filters
assets/img/           ← profile photo, share card and gallery photos
index.html            ← GENERATED home page, do not edit by hand
gallery/index.html    ← GENERATED Gallery page (only when there are photos)
```
