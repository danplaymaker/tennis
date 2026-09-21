# tennis

GSAP interaction studies. Open `prototypes/index.html` in a browser (no build step; GSAP 3.13 loads from jsDelivr).

- `prototypes/AUDIT.md` — audit of the interaction patterns studied, and the shortlist that was built.
- `prototypes/01…06-*.html` — one isolated demo per technique, placeholder content only, commented GSAP code.

The reference scrape lives in an ignored `lamalama.com/` folder and is never committed.

- `flowboard-ready/` — the same six demos rewritten for the Flowboard paste workflow (semantic classes, expanded CSS,
  CSS hover states, per-block convertibility flags). Each folder has `index.html` plus a generated `paste.md`; see
  `flowboard-ready/README.md`. Regenerate paste files with `python3 flowboard-ready/build_paste.py`.
