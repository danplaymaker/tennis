# Interaction audit (private R&D notes)

Source: a static scrape of an agency site (markup + inline CSS only). The compiled theme stylesheet and JS bundle
were **not** in the archive and the live site was unreachable from this environment, so everything below is inferred
from element structure, utility classes (Tailwind), `js-*` hooks and `data-*` attributes. No timings or easings were
recoverable from CSS; the values used in the prototypes are my own choices.

## Global architecture

| Hook | What it implies |
|---|---|
| `.js-scroller[data-swup-scroll-container] > .js-scroll-content` | Smooth-scroll wrapper/content pair (ScrollSmoother or Lenis shape) that Swup is told to scroll |
| `.js-loader .js-progress` (0 → `%`) | Full-screen preloader with a percentage counter, black bg, mono type |
| `.js-page-transition` (fixed, bg colour, z-8) + `.js-page-transition-counter` (z-9) | Page transitions = overlay fade + 0–100% counter, same visual language as the preloader |
| `data-swup-morph="lang-switch-item-*"`, `data-no-swup` | Swup morph plugin keeps these header nodes alive across navigations and morphs them instead of re-rendering |
| `data-component="…"` on every block | Component registry, JS instantiates per `data-component` |
| `<main data-theme="dark">` + `section[data-theme="dark\|none"]` + `.js-page-backdrop` | Per-section theme switching: a page-level backdrop element fades between colours as sections enter |
| `data-labels="A[/split/]B[/split/]C"` on section containers, `.js-header-message-container` | The header pill shows a random label from the current section's list, re-decoded on each section change |
| `data-logo="logo\|smile\|heart"` + `.ll-block--icon-grid` | Header icon is a pixel grid that morphs to a different glyph per section |

## Text patterns

**Mono text reveal** (`parts/mono_text_reveal`, 162× on the home page, 205× on Work)
```
.js-mono-text-reveal (relative)
  .js-animation-target.absolute.left-0.right-0.js-text-container  ← animated copy
  .opacity-0.js-text-container                                     ← invisible sizing copy
```
Two stacked copies in a monospace font: the ghost reserves the box, the absolute copy is animated (scramble/decode
style; the mono font keeps width stable while glyphs change). Variants: `data-delay="0.1|0.2|0.3"` on siblings for
stagger, `.js-mono-text-reveal-hover` (re-runs on hover), `.js-mono-text-reveal-label` (sticky bar), header message
swapping between labels, `data-text="Stay in the loop"` alt text on the "Follow us" label (swap on hover).

**Text reveal** (`parts/text_reveal`, headings + paragraphs): `.ll-text-reveal.opacity-0.js-text-reveal` with optional
`data-label="Not just pretty"` (small label injected above) and `data-indent="true"` (an empty inline-block
`.js-indent-item` spacer as the first child so the first line is indented). Starts at opacity 0 → line-based reveal
(SplitText-style) on scroll.

## Media patterns

- `[data-fade-in]` + `style="opacity:0"` + `data-loading="1|eager"` on every `img`/`video`: fade in once loaded and
  in view. Siblings carry `data-delay` for staggering.
- `parts/webgl_image` / `parts/webgl_video` with `.js-canvas` / `.js-upper-canvas`: images are drawn to a WebGL
  canvas (shader reveal / distortion). `data-parallax="true"` on some of them → scroll-linked offset.
  Not rebuilt in WebGL; the parallax is rebuilt in plain GSAP.
- `data-text="…"` on team images + `.js-cursor-label > .js-cursor-message` (fixed, pointer-events none, mono reveal
  inside): a cursor-following label that shows the image's caption on hover.
- Hero `section.mix-blend-exclusion` over an autoplaying backdrop video (`.js-backdrop-video-item`).
- `slides/logo_marquee` → `.js-marquee-container.w-max.gap-x-14.pr-14`: infinite horizontal marquee (not built; trivial
  with `xPercent:-100, repeat:-1, ease:none` on a duplicated track).
- Sticky side panels (`.js-sticky-item`, `position: sticky`, `( + / − )` toggles) with showreel preview / pitchdeck
  thumbnails; a sticky bottom bar (`.js-sticky-bar`) with mono labels + a live clock (`.js-clock` with a blinking dot).

## Case list (`blocks/case_highlighted` › `blocks/case_item`)

Each case is a `<button class="js-case-item" data-slug data-tag*>` containing:
- title, tag chips (mono reveals with `data-delay` stagger), `( View + )` where `.js-view-hover` scrambles and
  `.js-plus/.js-minus` swap;
- `.js-highlighted-images` — an absolutely positioned strip of 3 small thumbs (`width: 96/180rem-ish`, descending
  `z-index`, `.js-image-item > .js-image-inner`);
- `.js-content-slider.swiper.absolute` — a hidden Swiper track with sized slide placeholders
  (`320/600px` desktop, `128/240px` mobile) that the images move into when the row expands;
- `.js-zoom-button` "View case" (opacity 0, pointer-events none until expanded).

Read as: **click a row → thumbnails morph into a large draggable slider, other rows collapse** (Flip-style), plus tag
filtering on the Work page (`.js-tag-item[data-tag]`, `.js-active-item` overlay swap).

## Navigation

Fixed centred pill (`.js-menu`, `max-w 438px`, `backdrop-blur`, `opacity-0` until loaded): logo grid, centred message,
burger (`.js-top/.js-middle/.js-bottom` bars). `.js-menu-items-container` starts `h-0 overflow-hidden` and expands.
Each `.js-nav-item` contains: `.js-backdrop` (opacity 0), `.js-line` (`scale-x-0 origin-left`), `.js-text`
(`clip-path: inset(0 0 100% 0)` → revealed), and `.js-nav-item-icon` with 4 stacked pixel-SVG frames
(`.js-icon`, `.js-icon-mid`, `.js-icon-mid-second`, `.js-icon-alt`) that cycle like a sprite. Dropdown children use
`.js-dot`. A full-screen `.js-menu-blur` (`backdrop-blur-lg bg-black/40`) sits behind the open menu.

## Buttons and cards

`parts/buttons/button`: `.js-backdrop-hover` (fill, opacity 0) · `.js-inner` (border, `.js-text` mono reveal,
`.js-arrow origin-top-right`) · `.js-hover-inner` (absolute, inverted colour, `.js-text-hover opacity-0`,
`.js-arrow-hover origin-bottom-left scale-0`). Hover = fill in, text swap, arrow leaves top-right while a second arrow
grows in from bottom-left. `blocks/contact_card`: avatar + label, `.js-backdrop` fill, `.js-contact-card-reveal-hover`
label pre-positioned at the right that appears on hover. `data-prevent-hover` opts an element out.

## Prioritised shortlist (built)

1. **Mono text reveal** — the site's signature; everywhere. → `01`
2. **Scroll reveals + section theme** — SplitText lines, media batch stagger, body-colour tween, header label cycling. → `02`
3. **Smooth scroll + parallax + cursor label** — ScrollSmoother shape, manual scrub vs `data-speed`, quickTo follower. → `03`
4. **Case list morph** — Flip for filter reflow and thumbnail→slider expansion, Draggable + Inertia. → `04`
5. **Preloader + page transitions** — counter overlay, async out/swap/in, persistent header morph. → `05`
6. **Nav pill + button micro-interactions** — paused timelines, height:auto, clip-path, icon frame cycling. → `06`

Not built: WebGL image shaders, logo marquee, video modal/showreel, sticky side panels, clock, pitchdeck slides.
