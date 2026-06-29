# pro42good.me

Retro blue static tool hub for Pro42good projects, links, status notes, and experiments.

## About

- Plain HTML and CSS.
- No browser JavaScript.
- Designed for locked down browsers.
- Deployed with GitHub Pages.
- Public project metadata is generated during the Pages workflow.

## Build

```bash
python3 scripts/build_site.py
```

The build writes a deployable copy to `_site/` and injects public GitHub metadata into the homepage status panel. If GitHub metadata cannot be fetched, the build still succeeds with fallback status text.

Updated on 2026-06-29.
