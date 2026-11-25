# shruti-bt.github.io

Personal academic website, live at **https://shruti-bt.github.io**.

## How to update the site

All the text lives in three Markdown files. Edit them, push to `main`, and GitHub
rebuilds and publishes the site automatically.

| To change...                         | Edit                       |
|--------------------------------------|----------------------------|
| Name, role, photo, links, interests  | `content/about.md` (top settings block) |
| Bio paragraphs, "open to roles" box  | `content/about.md` (below the settings) |
| News & Highlights                    | `content/news.md`          |
| Papers and posters                   | `content/publications.md`  |

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
code: https://github.com/...
tag: Oral

```bibtex
@inproceedings{key2026,
  ...
}
```
````

Any `label: https://...` line becomes a button (`paper`, `code`, `video`, `project`, ...).

Formatting that works everywhere: `**bold**`, `*italic*`, `[link text](https://...)`.

## Previewing on your computer

```
python3 build.py
```

Then double-click `index.html` to open it in your browser. (`build.py` needs no
installs. Pushing to GitHub runs it for you, so this step is only for previewing.)

## Files

```
content/            ← the text (edit these)
template.html       ← page layout with {{placeholders}}
build.py            ← turns content/ + template.html into index.html
index.html          ← GENERATED, do not edit by hand
css/style.css       ← colours, fonts, spacing (theme variables at the top)
js/main.js          ← BibTeX toggle, sticky nav
assets/img/         ← profile photo and other images
```
