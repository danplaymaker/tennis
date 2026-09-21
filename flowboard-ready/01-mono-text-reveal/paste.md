# 01 · Mono text reveal — Flowboard paste snippets

Paste in this order: HTML, then CSS, then JS. Each fenced block is one paste. The GSAP scripts below go in **Project Settings → Custom Code → Footer** (before `</body>`), above the JS Embed:

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrollTrigger.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrambleTextPlugin.min.js"></script>
```

## 1. HTML — Header pill — fixed message that re-scrambles to a label from each section's data-labels.

```html
<div class="header-pill">
  <span class="mono-label header-pill__message">
    <span class="mono-label__anim" aria-hidden="true">[ scroll to begin ]</span>
    <span class="mono-label__ghost">[ SMALL BUT MIGHTY ]</span>
  </span>
</div>
```

## 2. HTML — Hero + four demo sections. Every .mono-label[data-reveal] decodes on scroll; data-delay staggers siblings.

```html
<section class="section section--hero">
  <div class="hero__stack">
    <span class="mono-label" data-reveal>
      <span class="mono-label__anim" aria-hidden="true">[ Lorem ipsum studio ]</span>
      <span class="mono-label__ghost">[ Lorem ipsum studio ]</span>
    </span>
    <h1 class="hero__title">Every small label<br>decodes into place.</h1>
    <p class="hero__lead">Scroll down. Each mono label scrambles from random glyphs to its final text, staggered by a data-delay attribute.</p>
  </div>
</section>

<section class="section" data-labels="DECODING TAGS[/split/]SMALL BUT MIGHTY[/split/]TYPE THAT TYPES">
  <h2 class="section__title">1 · Tags with data-delay stagger</h2>
  <div class="demo-stack">
    <div class="tag-row">
      <span class="tag"><span class="mono-label" data-reveal><span class="mono-label__anim" aria-hidden="true">Branding</span><span class="mono-label__ghost">Branding</span></span></span>
      <span class="tag"><span class="mono-label" data-reveal data-delay="0.1"><span class="mono-label__anim" aria-hidden="true">Corporate</span><span class="mono-label__ghost">Corporate</span></span></span>
      <span class="tag"><span class="mono-label" data-reveal data-delay="0.2"><span class="mono-label__anim" aria-hidden="true">Experience</span><span class="mono-label__ghost">Experience</span></span></span>
      <span class="tag"><span class="mono-label" data-reveal data-delay="0.3"><span class="mono-label__anim" aria-hidden="true">Campaign</span><span class="mono-label__ghost">Campaign</span></span></span>
    </div>
    <div class="tag-row">
      <span class="mono-label mono-label--dim" data-reveal><span class="mono-label__anim" aria-hidden="true">[ 20+ placeholder people ]</span><span class="mono-label__ghost">[ 20+ placeholder people ]</span></span>
      <span class="mono-label mono-label--dim" data-reveal data-delay="0.15"><span class="mono-label__anim" aria-hidden="true">[ Somewhere based ]</span><span class="mono-label__ghost">[ Somewhere based ]</span></span>
      <span class="mono-label mono-label--dim" data-reveal data-delay="0.3"><span class="mono-label__anim" aria-hidden="true">[ Est. 20XX ]</span><span class="mono-label__ghost">[ Est. 20XX ]</span></span>
    </div>
  </div>
</section>

<section class="section" data-labels="HOVER THE LINKS[/split/]GO ON, TOUCH THEM">
  <h2 class="section__title">2 · Hover re-scramble</h2>
  <div class="link-list">
    <a href="#" class="link-list__item" data-reveal-hover><span class="mono-label"><span class="mono-label__anim" aria-hidden="true">instagram</span><span class="mono-label__ghost">instagram</span></span></a>
    <a href="#" class="link-list__item" data-reveal-hover><span class="mono-label"><span class="mono-label__anim" aria-hidden="true">linkedin</span><span class="mono-label__ghost">linkedin</span></span></a>
    <a href="#" class="link-list__item" data-reveal-hover><span class="mono-label"><span class="mono-label__anim" aria-hidden="true">newsletter</span><span class="mono-label__ghost">newsletter</span></span></a>
  </div>
</section>

<section class="section" data-labels="TEXT THAT SWAPS[/split/]A TO B VIA NOISE">
  <h2 class="section__title">3 · Swap A → B through noise</h2>
  <div class="demo-stack">
    <span class="mono-label mono-label--large swap-label"><span class="mono-label__anim" aria-hidden="true">Follow us</span><span class="mono-label__ghost">Stay in the loop</span></span>
    <div><button class="small-button swap-button" type="button">Swap label</button></div>
    <p class="help-text">The ghost copy holds the longest of the two strings so the box never changes size.</p>
  </div>
</section>

<section class="section" data-labels="NO PLUGIN NEEDED[/split/]THE MANUAL WAY">
  <h2 class="section__title">4 · DIY scramble (no plugin)</h2>
  <div class="demo-stack">
    <div class="diy-text">HANDMADE SCRAMBLE</div>
    <div><button class="small-button diy-button" type="button">Replay</button></div>
  </div>
</section>
<div class="spacer"></div>
```

## 3. CSS — Page base — body colours and type. Skip if your Webflow site already sets these.

```css
*, *::before, *::after { box-sizing: border-box; }   /* Webflow default; keeps min-height/aspect-ratio maths sane */
body { margin: 0; background-color: #111111; color: #f1efe8; font-family: system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.4; }
.section { padding: 120px 40px; border-top: 1px solid rgba(241, 239, 232, 0.2); }
.section--hero { min-height: 100vh; display: flex; align-items: flex-end; border-top: 0; padding-bottom: 8vh; }
.section__title { font-size: 48px; line-height: 1.05; letter-spacing: -0.02em; font-weight: 500; margin: 0 0 32px 0; }
.hero__stack { display: flex; flex-direction: column; gap: 20px; }
.hero__title { font-size: 80px; line-height: 0.98; letter-spacing: -0.03em; font-weight: 500; margin: 0; }
.hero__lead { font-size: 18px; max-width: 36ch; color: rgba(241, 239, 232, 0.55); margin: 0; }
.spacer { height: 60vh; }
```

## 4. CSS — Mono label component — two stacked copies; the ghost holds the box, the anim copy is scrambled.

```css
.mono-label { position: relative; display: inline-block; font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; white-space: nowrap; }
.mono-label__anim { position: absolute; left: 0; right: 0; top: 0; }
.mono-label__ghost { opacity: 0; }
.mono-label--dim { color: rgba(241, 239, 232, 0.55); }
.mono-label--large { font-size: 19px; }
.tag { display: inline-flex; align-items: center; height: 22px; padding: 0 8px; background-color: #1f1f1f; color: #f1efe8; border-radius: 2px; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.demo-stack { display: flex; flex-direction: column; gap: 20px; }
.header-pill { position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 40; padding: 12px 16px; border-radius: 6px; background-color: rgba(31, 31, 31, 0.7); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); }
.link-list { max-width: 420px; }
.link-list__item { display: block; padding: 14px 0; border-bottom: 1px solid rgba(241, 239, 232, 0.2); color: inherit; text-decoration: none; }
.link-list__item:hover { color: #ff4d2e; }
.small-button { display: inline-flex; align-items: center; height: 30px; padding: 0 12px; background-color: #1f1f1f; color: #f1efe8; border: 1px solid rgba(241, 239, 232, 0.2); border-radius: 4px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; cursor: pointer; }
.small-button:hover { background-color: #f1efe8; color: #111111; }
.small-button:focus-visible { outline: 2px solid #ff4d2e; outline-offset: 2px; }
.diy-text { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 24px; }
.help-text { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; color: rgba(241, 239, 232, 0.55); margin: 0; }
```

## 5. JS — Scramble reveals. Everything here uses ScrambleTextPlugin, so the whole file is an Embed in Webflow.

```js
gsap.registerPlugin(ScrollTrigger, ScrambleTextPlugin);
const NOISE = "[]/\\|<>-_=+*#%&01";

/* [FLOWBOARD: EMBED ONLY] ScrambleTextPlugin has no Interactions equivalent.
 * Helper: scramble a .mono-label's animated copy to a target string. */
function scrambleTo(wrap, text, opts = {}) {
  const anim = wrap.querySelector(".mono-label__anim");
  const final = text ?? wrap.querySelector(".mono-label__ghost").textContent;
  return gsap.to(anim, {
    duration: opts.duration ?? 0.8, delay: opts.delay ?? 0, ease: "none",
    scrambleText: { text: final, chars: NOISE, speed: 0.6, revealDelay: 0.15, tweenLength: false },
    overwrite: "auto"
  });
}

/* [FLOWBOARD: EMBED ONLY] Scroll-in decode (ScrollTrigger is convertible on its own, but the tween is a scramble).
 * Pre-fill each animated copy with noise so nothing shows before its trigger. */
gsap.utils.toArray(".mono-label[data-reveal]").forEach(wrap => {
  const anim = wrap.querySelector(".mono-label__anim");
  const final = anim.textContent;
  anim.textContent = final.replace(/\S/g, () => NOISE[Math.floor(Math.random() * NOISE.length)]);
  ScrollTrigger.create({ trigger: wrap, start: "top 90%", once: true,
    onEnter: () => scrambleTo(wrap, final, { delay: parseFloat(wrap.dataset.delay || 0) }) });
});

/* [FLOWBOARD: EMBED ONLY] Hover re-scramble. The colour change on hover is plain CSS (.link-list__item:hover). */
gsap.utils.toArray("[data-reveal-hover]").forEach(link => {
  link.addEventListener("mouseenter", () => scrambleTo(link.querySelector(".mono-label"), null, { duration: 0.5 }));
});

/* [FLOWBOARD: EMBED ONLY] Swap between two strings on click. */
const swapWrap = document.querySelector(".swap-label");
const swapTexts = ["Follow us", "Stay in the loop"];
let swapIndex = 0;
document.querySelector(".swap-button").addEventListener("click", () => {
  swapIndex = 1 - swapIndex;
  scrambleTo(swapWrap, swapTexts[swapIndex], { duration: 0.7 });
});

/* [FLOWBOARD: EMBED ONLY] Header pill: each section with data-labels picks a random label on enter (both directions). */
const headerMsg = document.querySelector(".header-pill__message");
gsap.utils.toArray("[data-labels]").forEach(section => {
  const labels = section.dataset.labels.split("[/split/]");
  const pick = () => scrambleTo(headerMsg, "[ " + gsap.utils.random(labels) + " ]", { duration: 0.6 });
  ScrollTrigger.create({ trigger: section, start: "top 50%", end: "bottom 50%", onEnter: pick, onEnterBack: pick });
});

/* [FLOWBOARD: EMBED ONLY] DIY scramble: tween a number 0→1 and rebuild the string each frame (no plugin). */
const diy = document.querySelector(".diy-text");
const diyText = diy.textContent;
function diyScramble() {
  const proxy = { p: 0 };
  gsap.to(proxy, { p: 1, duration: 1.2, ease: "power2.out", onUpdate() {
    const lock = Math.floor(proxy.p * diyText.length);
    diy.textContent = diyText.split("").map((ch, i) => ch === " " ? " " : (i < lock ? ch : NOISE[Math.floor(Math.random() * NOISE.length)])).join("");
  } });
}
document.querySelector(".diy-button").addEventListener("click", diyScramble);
ScrollTrigger.create({ trigger: diy, start: "top 85%", once: true, onEnter: diyScramble });
```
