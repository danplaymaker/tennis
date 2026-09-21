# Flowboard-ready prototypes

Parallel output of `/prototypes`, rewritten for the Flowboard paste workflow (HTML/CSS/JS → native Webflow elements,
styles and Interactions). Private R&D, placeholder content only.

Each folder has:

- `index.html` — full working page (semantic classes, expanded CSS, GSAP from jsDelivr) to sanity-check in a browser.
- `paste.md` — the same page cut into paste-sized HTML, CSS and JS blocks with a one-line note each.
  `paste.md` is generated from `index.html` marker comments, so the two never drift.

Conventions used in every file:

- One semantic class per style, BEM-ish (`.case-row`, `.case-row__thumb`, `.case-row__thumb--large`). No utilities, no hashes.
- Hover and focus are CSS `:hover` / `:focus-visible` wherever a CSS state is enough. JS only drives non-hover state
  (open/closed, active filter, scroll position).
- GSAP targets classes only, never IDs. Every JS block is headed by `[FLOWBOARD: CONVERTIBLE]` or
  `[FLOWBOARD: EMBED ONLY]`. Embed-only blocks go in a Webflow **Embed** element (or footer custom code) unchanged.
- The GSAP `<script src>` tags belong in Project Settings → Custom Code → Footer, before the Embed.

## Per-prototype summary

### 01 · Mono text reveal

| Converts | Stays as Embed |
|---|---|
| All styles; `.link-list__item:hover`, `.small-button:hover` | Everything in the JS: every block uses ScrambleTextPlugin (scroll-in decode, hover re-scramble, A→B swap, header label cycling, DIY scramble). |

Gotchas: keep the two-copy structure (`.mono-label__anim` absolute over `.mono-label__ghost` invisible) as two text
elements inside a relative wrapper. `data-reveal`, `data-delay`, `data-labels` are custom attributes on the element
settings panel. The ghost must carry the longest string the label will ever show.

### 02 · Scroll reveals + section themes

| Converts | Stays as Embed |
|---|---|
| Media fade-in: one "scroll into view" per `[data-fade-in]`, opacity/y/scale tween, `data-delay` as delay. | SplitText text reveal (`mask: "lines"`, `autoSplit`), the scrambled `data-label`, header pill scramble. |
| Section theme: body background-color + color tween when `[data-theme]` crosses viewport middle (both directions). | |

Gotchas: colours are tweened as real `background-color` / `color` values, not CSS variables, so Interactions can take them.
Elements start at `opacity: 0` in CSS to avoid a flash; if you convert the reveal to an IX, set the initial state there
instead. The `.text-reveal__label` and `.text-reveal__indent` elements are injected by JS; in Webflow add them as real
elements and delete those two lines.

### 03 · Smooth scroll, parallax, cursor label

| Converts | Stays as Embed |
|---|---|
| Manual parallax on `[data-parallax]`: "while scrolling in view" from −X% to +X% on `.parallax-frame__layer`, 0% at top-enters-bottom, 100% at bottom-leaves-top. | ScrollSmoother (and its `data-speed` / `data-lag` effects). Cursor label (quickTo follower + ScrambleText). |

Gotchas: ScrollSmoother needs `.smooth-wrapper > .smooth-content` around the whole page body. Webflow does not give you
that structure; add two divs at the top of the Body and move every section inside `.smooth-content`. Anything `position:
fixed` (the cursor label, a fixed nav) must sit **outside** the wrapper. `mix-blend-mode: exclusion` on `.hero__content`
is a plain style and converts fine. `cursor: none` on frames hides the OS cursor; drop it if you skip the cursor label.

### 04 · Case list: filter + expand

| Converts | Stays as Embed |
|---|---|
| All styles; thumb lift on row hover (`:hover` + `transition-delay` stagger); `.case-filter__button:hover`; CTA fade (basic opacity tween, could be a class-change IX on `.is-open`). | Everything else: Flip for expand/collapse and for filter reflow, Draggable + InertiaPlugin on the open track. |

Gotchas: rows are static markup (no JS templating), so each row's three strip thumbs plus its hidden track thumbs are
real elements. Open/closed sizing lives in CSS under `.is-open`; Flip animates the difference. The track must be
`width: max-content` for Draggable bounds to be measured correctly. Row click uses the `.case-row` cursor pointer;
`.case-row__cta` is a real link and stops propagation by class check.

### 05 · Preloader + page transitions

| Converts | Stays as Embed |
|---|---|
| Preloader fade-out (page-load IX), overlay + counter opacity fades (link-click / page-load IX), page image fade/slide. | The 0–100 counters (object tween + snap), SplitText title reveal, header title ScrambleText, `<template>` swap and history routing. |

Gotchas: `<template>` pages are a stand-in for real pages. In Webflow use real pages and either Swup (the studied site's
approach, with `data-swup-morph` on elements that persist) or Webflow's native page-load / link-click Interactions for the
overlay. The persistent header only works with Swup or a single-page setup. The overlay is `pointer-events: none`, so
clicks during a transition are blocked by the `busy` flag, not the overlay.

### 06 · Nav pill + buttons

| Converts | Stays as Embed |
|---|---|
| Buttons and contact cards: 100% CSS `:hover` / `:focus-visible` (fill, text swap, diagonal arrow hand-off with `transition-delay`). Nav item hover backdrop: CSS. Menu open timeline `openTl`: blur opacity, burger → X, panel height, line scaleX stagger. | `extraTl`: clip-path text reveal, ScrambleText message, stepped icon-frame cycling. |

Gotchas: `height: "auto"` in the open timeline becomes a fixed pixel height in Interactions (measure the open panel).
Both timelines are played/reversed together on the same click; if you convert `openTl`, keep `extraTl` in the Embed
and trigger it from the same click handler. Pixel icons are four stacked inline SVGs per item; the last carries
`.nav-item__icon-frame--final` and is the resting frame.

## Shared gotchas

- **Custom attributes** (`data-*`) are how the JS finds targets and reads options. Add them in Webflow's element settings.
- **`:focus-visible`** is included next to every `:hover` so keyboard users get the same state; Webflow's hover selector
  won't carry it, so keep the focus rule in the Embed CSS if you care about it.
- **Placeholder images** are `background-color` + a repeating gradient. Swap for real `<img>` elements; the classes stay.
- **GSAP 3.13** makes every plugin used here free (SplitText, ScrambleText, Flip, Draggable, Inertia, ScrollSmoother).
- **Reduced motion** is not handled here; wrap the Embed JS in `gsap.matchMedia()` if you ship it.
