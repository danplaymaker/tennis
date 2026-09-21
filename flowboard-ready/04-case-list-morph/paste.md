# 04 · Case list: filter + expand — Flowboard paste snippets

Paste in this order: HTML, then CSS, then JS. Each fenced block is one paste. The GSAP scripts below go in **Project Settings → Custom Code → Footer** (before `</body>`), above the JS Embed:

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/Flip.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/Draggable.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/InertiaPlugin.min.js"></script>
```

## 1. HTML — Intro + filter bar. data-filter values match each row's data-tags.

```html
<section class="section">
  <p class="section__eyebrow">[ Placeholder work ]</p>
  <h1 class="section__title">Click a row to expand its images into a draggable strip. Filter to reflow.</h1>
  <div class="case-filter">
    <button class="case-filter__button is-active" type="button" data-filter="all">All</button>
    <button class="case-filter__button" type="button" data-filter="branding">Branding</button>
    <button class="case-filter__button" type="button" data-filter="web">Web</button>
    <button class="case-filter__button" type="button" data-filter="campaign">Campaign</button>
  </div>
```

## 2. HTML — Case list — four rows. The first three thumbs live in the strip; extra images wait in the hidden track.

```html
  <div class="case-list">
    <div class="case-row" data-tags="branding web">
      <div class="case-row__head">
        <div><h3 class="case-row__title">Project Alpha</h3><a class="case-row__cta" href="#">View case →</a></div>
        <div class="case-row__tags"><span class="tag">branding</span><span class="tag">web</span></div>
        <div class="case-row__toggle">( View <span class="case-row__toggle-plus">+</span><span class="case-row__toggle-minus">−</span> )</div>
        <div class="case-row__thumbs">
          <div class="case-row__thumb case-row__thumb--small case-row__thumb--blue"></div>
          <div class="case-row__thumb case-row__thumb--large case-row__thumb--brown"></div>
          <div class="case-row__thumb case-row__thumb--small case-row__thumb--green"></div>
        </div>
      </div>
      <div class="case-row__slider"><div class="case-row__track">
        <div class="case-row__thumb case-row__thumb--large case-row__thumb--purple"></div>
        <div class="case-row__thumb case-row__thumb--small case-row__thumb--olive"></div>
      </div></div>
    </div>

    <div class="case-row" data-tags="campaign">
      <div class="case-row__head">
        <div><h3 class="case-row__title">Project Beta</h3><a class="case-row__cta" href="#">View case →</a></div>
        <div class="case-row__tags"><span class="tag">campaign</span></div>
        <div class="case-row__toggle">( View <span class="case-row__toggle-plus">+</span><span class="case-row__toggle-minus">−</span> )</div>
        <div class="case-row__thumbs">
          <div class="case-row__thumb case-row__thumb--small case-row__thumb--brown"></div>
          <div class="case-row__thumb case-row__thumb--large case-row__thumb--teal"></div>
          <div class="case-row__thumb case-row__thumb--small case-row__thumb--blue"></div>
        </div>
      </div>
      <div class="case-row__slider"><div class="case-row__track">
        <div class="case-row__thumb case-row__thumb--large case-row__thumb--green"></div>
      </div></div>
    </div>

    <div class="case-row" data-tags="web">
      <div class="case-row__head">
        <div><h3 class="case-row__title">Project Gamma</h3><a class="case-row__cta" href="#">View case →</a></div>
        <div class="case-row__tags"><span class="tag">web</span></div>
        <div class="case-row__toggle">( View <span class="case-row__toggle-plus">+</span><span class="case-row__toggle-minus">−</span> )</div>
        <div class="case-row__thumbs">
          <div class="case-row__thumb case-row__thumb--small case-row__thumb--green"></div>
          <div class="case-row__thumb case-row__thumb--large case-row__thumb--purple"></div>
          <div class="case-row__thumb case-row__thumb--small case-row__thumb--teal"></div>
        </div>
      </div>
      <div class="case-row__slider"><div class="case-row__track">
        <div class="case-row__thumb case-row__thumb--large case-row__thumb--brown"></div>
        <div class="case-row__thumb case-row__thumb--small case-row__thumb--olive"></div>
        <div class="case-row__thumb case-row__thumb--large case-row__thumb--blue"></div>
      </div></div>
    </div>

    <div class="case-row" data-tags="branding campaign">
      <div class="case-row__head">
        <div><h3 class="case-row__title">Project Delta</h3><a class="case-row__cta" href="#">View case →</a></div>
        <div class="case-row__tags"><span class="tag">branding</span><span class="tag">campaign</span></div>
        <div class="case-row__toggle">( View <span class="case-row__toggle-plus">+</span><span class="case-row__toggle-minus">−</span> )</div>
        <div class="case-row__thumbs">
          <div class="case-row__thumb case-row__thumb--small case-row__thumb--purple"></div>
          <div class="case-row__thumb case-row__thumb--large case-row__thumb--blue"></div>
          <div class="case-row__thumb case-row__thumb--small case-row__thumb--teal"></div>
        </div>
      </div>
      <div class="case-row__slider"><div class="case-row__track">
        <div class="case-row__thumb case-row__thumb--large case-row__thumb--olive"></div>
      </div></div>
    </div>
  </div>
  <div class="divider"></div>
</section>
```

## 3. CSS — Page base + filter bar. Active filter is a JS-toggled .is-active class (not a hover state).

```css
*, *::before, *::after { box-sizing: border-box; }   /* Webflow default; keeps min-height/aspect-ratio maths sane */
body { margin: 0; background-color: #111111; color: #f1efe8; font-family: system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.4; }
.section { padding: 120px 40px; }
.section__eyebrow { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; color: rgba(241, 239, 232, 0.55); margin: 0 0 24px 0; }
.section__title { font-size: 48px; line-height: 1.05; letter-spacing: -0.02em; font-weight: 500; margin: 0 0 40px 0; max-width: 24ch; }
.case-filter { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 40px; }
.case-filter__button { display: inline-flex; align-items: center; height: 22px; padding: 0 8px; background-color: #1f1f1f; color: #f1efe8; border: 0; border-radius: 2px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; text-transform: uppercase; opacity: 0.55; cursor: pointer; }
.case-filter__button:hover { opacity: 0.85; }
.case-filter__button:focus-visible { outline: 2px solid #ff4d2e; outline-offset: 2px; }
.case-filter__button.is-active { opacity: 1; background-color: #f1efe8; color: #111111; }
.divider { height: 1px; background-color: rgba(241, 239, 232, 0.2); }
```

## 4. CSS — Case row. Collapsed vs .is-open sizes; thumb lift on hover is pure CSS with staggered transition-delay.

```css
.case-row { position: relative; width: 100%; border-top: 1px solid rgba(241, 239, 232, 0.2); padding: 24px 0; overflow: hidden; cursor: pointer; }
.case-row__head { display: grid; grid-template-columns: 2fr 3fr 1fr 6fr; gap: 16px; align-items: start; }
.case-row__title { font-size: 18px; font-weight: 500; margin: 0; }
.case-row__cta { display: inline-flex; align-items: center; height: 40px; margin-top: 16px; padding: 0 14px; border: 1px solid rgba(241, 239, 232, 0.2); border-radius: 6px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; text-transform: uppercase; color: inherit; text-decoration: none; opacity: 0; pointer-events: none; }
.case-row__cta:hover { background-color: #f1efe8; color: #111111; }
.case-row.is-open .case-row__cta { pointer-events: auto; }
.case-row__tags { display: flex; gap: 2px; flex-wrap: wrap; }
.tag { display: inline-flex; align-items: center; height: 22px; padding: 0 8px; background-color: #1f1f1f; color: #f1efe8; border-radius: 2px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; text-transform: uppercase; }
.case-row__toggle { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; }
.case-row__toggle-minus { display: none; }
.case-row.is-open .case-row__toggle-plus { display: none; }
.case-row.is-open .case-row__toggle-minus { display: inline; }
.case-row__thumbs { display: flex; gap: 8px; justify-content: flex-end; height: 120px; }
.case-row__thumb { flex-shrink: 0; height: 100%; border-radius: 6px; background-color: #3a3a3a; background-image: repeating-linear-gradient(135deg, rgba(255,255,255,0.06) 0 6px, transparent 6px 14px); transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1); }
.case-row__thumb--small { width: 96px; }
.case-row__thumb--large { width: 180px; }
.case-row__thumb--blue { background-color: #4a5d73; } .case-row__thumb--brown { background-color: #7a5a45; } .case-row__thumb--green { background-color: #4f6b52; } .case-row__thumb--purple { background-color: #6b4f6b; } .case-row__thumb--olive { background-color: #8a7a3a; } .case-row__thumb--teal { background-color: #3d5c6b; }
.case-row:not(.is-open):hover .case-row__thumbs .case-row__thumb { transform: translateY(-8px); }
.case-row__thumbs .case-row__thumb:nth-child(2) { transition-delay: 0.04s; }
.case-row__thumbs .case-row__thumb:nth-child(3) { transition-delay: 0.08s; }
.case-row__slider { height: 0; overflow: hidden; margin-top: 0; }
.case-row.is-open .case-row__slider { height: 400px; margin-top: 56px; }
.case-row__track { position: relative; display: flex; gap: 12px; height: 100%; width: max-content; cursor: grab; }
.case-row__track:active { cursor: grabbing; }
.case-row.is-open .case-row__thumb--small { width: 320px; }
.case-row.is-open .case-row__thumb--large { width: 600px; }
@media (max-width: 900px) { .case-row__head { grid-template-columns: 1fr 1fr; } .case-row__thumbs { grid-column: 1 / -1; justify-content: flex-start; } }
```

## 5. JS — Expand/collapse + filter with Flip, draggable strip. All Embed-only (Flip, Draggable, InertiaPlugin).

```js
gsap.registerPlugin(Flip, Draggable, InertiaPlugin);
let openRow = null;
let drag = null;

/* [FLOWBOARD: EMBED ONLY] Flip: getState → move thumbs into the track + toggle .is-open → Flip.from.
 * The row itself is in the state so its height change (from CSS) animates too. */
function toggleRow(row) {
  const opening = !row.classList.contains("is-open");
  const rows = gsap.utils.toArray(".case-row");
  const thumbs = row.querySelectorAll(".case-row__thumb");
  const track = row.querySelector(".case-row__track");
  const strip = row.querySelector(".case-row__thumbs");
  const targets = [row, ...thumbs];
  if (openRow && openRow !== row) targets.push(openRow, ...openRow.querySelectorAll(".case-row__thumb"));
  const state = Flip.getState(targets);

  if (openRow && openRow !== row) collapseDOM(openRow);
  if (opening) {
    row.classList.add("is-open");
    track.prepend(...Array.from(strip.querySelectorAll(".case-row__thumb")));
    openRow = row;
  } else {
    collapseDOM(row);
    openRow = null;
  }
  gsap.set(rows.filter(r => r !== row), { clearProps: "height" });

  Flip.from(state, {
    duration: 0.9, ease: "power3.inOut",
    absolute: ".case-row__thumb", nested: true, stagger: 0.03,
    onComplete: () => { gsap.set(row, { clearProps: "height" }); if (opening) makeDraggable(row); }
  });
  /* [FLOWBOARD: CONVERTIBLE] the CTA fade is a basic opacity tween (could be a "class change" IX on .is-open). */
  gsap.to(row.querySelector(".case-row__cta"), { opacity: opening ? 1 : 0, duration: 0.4, delay: opening ? 0.5 : 0 });
}

function collapseDOM(row) {
  row.classList.remove("is-open");
  const thumbs = Array.from(row.querySelectorAll(".case-row__thumb"));
  gsap.set(thumbs, { clearProps: "transform" });
  row.querySelector(".case-row__thumbs").append(...thumbs.slice(0, 3));
  gsap.to(row.querySelector(".case-row__cta"), { opacity: 0, duration: 0.2 });
  if (drag) { drag.kill(); drag = null; }
}

/* [FLOWBOARD: EMBED ONLY] Draggable + InertiaPlugin on the open track. */
function makeDraggable(row) {
  const track = row.querySelector(".case-row__track");
  const slider = row.querySelector(".case-row__slider");
  drag = Draggable.create(track, {
    type: "x", inertia: true, edgeResistance: 0.85, cursor: "grab",
    bounds: slider,                              // the track's edges may never pass the slider frame's edges
    onPress() { this.applyBounds(slider); }      // re-measure on every press in case layout changed since opening
  })[0];
}

gsap.utils.toArray(".case-row").forEach(row => {
  row.addEventListener("click", e => {
    if (e.target.closest(".case-row__track") && row.classList.contains("is-open")) return;
    if (e.target.closest(".case-row__cta")) return;
    toggleRow(row);
  });
});

/* [FLOWBOARD: EMBED ONLY] Filter with Flip: rows that leave fade out, rows that enter fade in, survivors slide. */
document.querySelector(".case-filter").addEventListener("click", e => {
  const btn = e.target.closest("[data-filter]");
  if (!btn) return;
  document.querySelectorAll(".case-filter__button").forEach(b => b.classList.toggle("is-active", b === btn));
  const filter = btn.dataset.filter;
  const rows = gsap.utils.toArray(".case-row");
  if (openRow) toggleRow(openRow);
  const state = Flip.getState(rows);
  rows.forEach(r => r.style.display = (filter === "all" || r.dataset.tags.split(" ").includes(filter)) ? "" : "none");
  Flip.from(state, {
    duration: 0.7, ease: "power3.inOut", absolute: true,
    onEnter: els => gsap.fromTo(els, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.5, delay: 0.2 }),
    onLeave: els => gsap.to(els, { opacity: 0, y: -20, duration: 0.3 })
  });
});
```
