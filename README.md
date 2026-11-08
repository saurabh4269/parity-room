# The project page

A static page: `index.html`, `assets/site.css`, `assets/app.js`, the images in `assets/img/` and two self-hosted fonts. No build step, no analytics, and nothing from another site loads until a visitor presses play on the film (Vimeo).

Every picture is a frame of the recorded film or a screenshot of Switch's own UI. The page has no player or dashboard of its own. The frames in `assets/img/` are un-zoomed renders of the recording, and `assets/img/zoom/` holds the zoomed frames from the film that open when a figure is clicked.

## Preview
```bash
python3 -m http.server 8123 --directory site     # then open http://127.0.0.1:8123/
```

## Publish
GitHub Pages serves the `gh-pages` branch, which holds the contents of this folder at its root:
```bash
git subtree split --prefix site -b gh-pages-tmp && git push -f origin gh-pages-tmp:gh-pages && git branch -D gh-pages-tmp
```

## Fonts
Bricolage Grotesque and Martian Mono, both under the SIL Open Font License 1.1. See [`assets/fonts/NOTICE.md`](assets/fonts/NOTICE.md).
