# 03 · Smooth scroll, parallax, cursor label — Flowboard paste snippets

Paste in this order: HTML, then CSS, then JS. Each fenced block is one paste. The GSAP scripts below go in **Project Settings → Custom Code → Footer** (before `</body>`), above the JS Embed:

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrollTrigger.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrollSmoother.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrambleTextPlugin.min.js"></script>
```

## 1. HTML — Cursor label — fixed, follows the pointer, shows the hovered frame's data-text. Place outside the smoother wrapper.

```html
<div class="cursor-label"><span class="cursor-label__tag">label</span></div>
```

## 2. HTML — Smoother wrapper/content with hero + gallery. data-parallax = manual scrub strength; data-speed / data-lag are read by ScrollSmoother.

```html
<div class="smooth-wrapper">
<div class="smooth-content">

  <section class="hero">
    <div class="hero__backdrop" data-speed="0.8"></div>
    <div class="hero__content">
      <p class="hero__eyebrow">[ Exclusion blend hero ]</p>
      <h1 class="hero__title">Scroll: the backdrop drifts<br>slower than the page.</h1>
    </div>
  </section>

  <section class="section">
    <h2 class="section__title">Manual parallax with scrub vs. ScrollSmoother data-speed</h2>
    <div class="gallery">
      <div class="parallax-frame gallery__item--one" data-parallax="0.6" data-text="Manual · 0.6"><div class="parallax-frame__layer parallax-frame__layer--blue"></div></div>
      <div class="parallax-frame gallery__item--two" data-parallax="1" data-text="Manual · 1"><div class="parallax-frame__layer parallax-frame__layer--brown"></div></div>
      <div class="parallax-frame gallery__item--three" data-speed="0.9" data-text="data-speed 0.9"><div class="parallax-frame__layer parallax-frame__layer--green"></div></div>
      <div class="parallax-frame gallery__item--four" data-lag="0.3" data-text="data-lag 0.3"><div class="parallax-frame__layer parallax-frame__layer--purple"></div></div>
      <div class="parallax-frame gallery__item--five" data-parallax="1.4" data-text="Manual · 1.4"><div class="parallax-frame__layer parallax-frame__layer--olive"></div></div>
    </div>
  </section>

  <section class="section">
    <h2 class="section__title">Hover any block: a label follows the cursor and scrambles in.</h2>
    <p class="section__lead">The label text comes from a data-text attribute on the frame.</p>
  </section>
  <div class="spacer"></div>

</div>
</div>
```

## 3. CSS — Page base + ScrollSmoother wrapper/content. In Webflow, wrap the whole page body in these two divs.

```css
*, *::before, *::after { box-sizing: border-box; }   /* Webflow default; keeps min-height/aspect-ratio maths sane */
body { margin: 0; background-color: #111111; color: #f1efe8; font-family: system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.4; }
.smooth-wrapper { position: fixed; inset: 0; overflow: hidden; }
.smooth-content { will-change: transform; }
.section { padding: 120px 40px; }
.section__title { font-size: 48px; line-height: 1.05; letter-spacing: -0.02em; font-weight: 500; margin: 0 0 40px 0; max-width: 26ch; }
.section__lead { font-size: 18px; max-width: 40ch; color: rgba(241, 239, 232, 0.55); margin: 0; }
.spacer { height: 30vh; }
```

## 4. CSS — Hero, parallax frames, gallery, cursor label.

```css
.hero { position: relative; min-height: 100vh; display: flex; align-items: flex-end; overflow: hidden; padding: 0 40px; }
.hero__backdrop { position: absolute; top: -20%; bottom: -20%; left: 0; right: 0; background-image: linear-gradient(120deg, #f1efe8 0 45%, #ff4d2e 45% 70%, #4a5d73 70%); }
.hero__content { position: relative; mix-blend-mode: exclusion; color: #ffffff; padding-bottom: 8vh; }
.hero__eyebrow { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; margin: 0 0 24px 0; }
.hero__title { font-size: 80px; line-height: 0.98; letter-spacing: -0.03em; font-weight: 500; margin: 0; }
.parallax-frame { position: relative; overflow: hidden; border-radius: 6px; aspect-ratio: 2 / 3; cursor: none; }
.parallax-frame__layer { position: absolute; top: -15%; bottom: -15%; left: 0; right: 0; background-color: #3a3a3a; background-image: repeating-linear-gradient(135deg, rgba(255,255,255,0.06) 0 6px, transparent 6px 14px); }
.parallax-frame__layer--blue { background-color: #4a5d73; }
.parallax-frame__layer--brown { background-color: #7a5a45; }
.parallax-frame__layer--green { background-color: #4f6b52; }
.parallax-frame__layer--purple { background-color: #6b4f6b; }
.parallax-frame__layer--olive { background-color: #8a7a3a; }
.gallery { display: grid; grid-template-columns: repeat(12, 1fr); gap: 16px; align-items: start; }
.gallery__item--one { grid-column: 1 / span 3; }
.gallery__item--two { grid-column: 4 / span 3; margin-top: 18vh; }
.gallery__item--three { grid-column: 8 / span 5; aspect-ratio: 4 / 3; }
.gallery__item--four { grid-column: 2 / span 5; aspect-ratio: 16 / 10; }
.gallery__item--five { grid-column: 8 / span 3; margin-top: -10vh; }
@media (max-width: 800px) { .gallery > .parallax-frame { grid-column: 1 / -1; margin-top: 0; } }
.cursor-label { position: fixed; left: 0; top: 0; z-index: 60; pointer-events: none; opacity: 0; }
.cursor-label__tag { display: inline-flex; align-items: center; height: 22px; padding: 0 8px; background-color: #1f1f1f; color: #f1efe8; border-radius: 2px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; text-transform: uppercase; white-space: nowrap; transform: translate(12px, -100%); }
```

## 5. JS — ScrollSmoother (Embed), scrubbed parallax (convertible), cursor label (Embed).

```js
gsap.registerPlugin(ScrollTrigger, ScrollSmoother, ScrambleTextPlugin);

/* [FLOWBOARD: EMBED ONLY] ScrollSmoother. Needs the .smooth-wrapper > .smooth-content structure around the page.
 * effects:true reads data-speed / data-lag from the markup. Remove this block to fall back to native scroll; the
 * manual parallax below still works. */
ScrollSmoother.create({ wrapper: ".smooth-wrapper", content: ".smooth-content", smooth: 1.2, effects: true, normalizeScroll: true });

/* [FLOWBOARD: CONVERTIBLE] Manual parallax = "while scrolling in view" from -X% to +X% on the inner layer,
 * 0% when the frame's top hits the viewport bottom, 100% when its bottom leaves the top. */
gsap.utils.toArray("[data-parallax]").forEach(frame => {
  const strength = parseFloat(frame.dataset.parallax) * 10;
  gsap.fromTo(frame.querySelector(".parallax-frame__layer"), { yPercent: -strength }, {
    yPercent: strength, ease: "none",
    scrollTrigger: { trigger: frame, start: "top bottom", end: "bottom top", scrub: true }
  });
});

/* [FLOWBOARD: EMBED ONLY] Cursor label: gsap.quickTo follower + ScrambleText. (Webflow's "mouse move in viewport"
 * IX can approximate the follow, but not the text scramble.) */
const label = document.querySelector(".cursor-label");
const labelText = document.querySelector(".cursor-label__tag");
const xTo = gsap.quickTo(label, "x", { duration: 0.35, ease: "power3" });
const yTo = gsap.quickTo(label, "y", { duration: 0.35, ease: "power3" });
window.addEventListener("mousemove", e => { xTo(e.clientX); yTo(e.clientY); });
gsap.utils.toArray("[data-text]").forEach(el => {
  el.addEventListener("mouseenter", () => {
    gsap.to(label, { opacity: 1, duration: 0.25, overwrite: "auto" });
    gsap.to(labelText, { duration: 0.5, scrambleText: { text: el.dataset.text, chars: "[]/\\|-_=+*#", speed: 0.6, tweenLength: false }, overwrite: "auto" });
  });
  el.addEventListener("mouseleave", () => gsap.to(label, { opacity: 0, duration: 0.25, overwrite: "auto" }));
});
```
