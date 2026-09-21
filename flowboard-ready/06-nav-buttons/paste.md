# 06 · Nav pill + button micro-interactions — Flowboard paste snippets

Paste in this order: HTML, then CSS, then JS. Each fenced block is one paste. The GSAP scripts below go in **Project Settings → Custom Code → Footer** (before `</body>`), above the JS Embed:

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrambleTextPlugin.min.js"></script>
```

## 1. HTML — Blur layer + nav pill. Each item stacks four pixel-icon frames (the last is the resting frame).

```html
<div class="menu-blur"></div>
<div class="nav-pill">
  <div class="nav-pill__bg"></div>
  <div class="nav-pill__bar">
    <svg class="nav-pill__logo" viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="0" width="2" height="2"/><rect x="4" y="0" width="2" height="2"/><rect x="8" y="0" width="2" height="2"/><rect x="2" y="2" width="2" height="2"/><rect x="6" y="2" width="2" height="2"/><rect x="0" y="4" width="2" height="2"/><rect x="4" y="4" width="2" height="2"/><rect x="8" y="4" width="2" height="2"/><rect x="2" y="6" width="2" height="2"/><rect x="6" y="6" width="2" height="2"/><rect x="0" y="8" width="2" height="2"/><rect x="4" y="8" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/></svg>
    <div class="nav-pill__message">[ menu ]</div>
    <button class="nav-pill__burger" type="button" aria-label="Toggle menu"><i class="nav-pill__burger-line nav-pill__burger-line--top"></i><i class="nav-pill__burger-line nav-pill__burger-line--middle"></i><i class="nav-pill__burger-line nav-pill__burger-line--bottom"></i></button>
  </div>
  <div class="nav-pill__items">
    <a class="nav-item" href="#"><span class="nav-item__bg"></span><span class="nav-item__line"></span>
      <span class="nav-item__icon">
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="0" width="2" height="2"/><rect x="4" y="2" width="2" height="2"/><rect x="8" y="4" width="2" height="2"/><rect x="2" y="6" width="2" height="2"/><rect x="6" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="2" y="0" width="2" height="2"/><rect x="6" y="2" width="2" height="2"/><rect x="0" y="4" width="2" height="2"/><rect x="4" y="6" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="4" y="0" width="2" height="2"/><rect x="8" y="2" width="2" height="2"/><rect x="2" y="4" width="2" height="2"/><rect x="6" y="6" width="2" height="2"/><rect x="0" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame nav-item__icon-frame--final" viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="0" width="2" height="2"/><rect x="8" y="0" width="2" height="2"/><rect x="4" y="4" width="2" height="2"/><rect x="0" y="8" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/></svg>
      </span><span class="nav-item__text">Work</span></a>
    <a class="nav-item" href="#"><span class="nav-item__bg"></span><span class="nav-item__line"></span>
      <span class="nav-item__icon">
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="0" width="2" height="2"/><rect x="4" y="2" width="2" height="2"/><rect x="8" y="4" width="2" height="2"/><rect x="2" y="6" width="2" height="2"/><rect x="6" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="2" y="0" width="2" height="2"/><rect x="6" y="2" width="2" height="2"/><rect x="0" y="4" width="2" height="2"/><rect x="4" y="6" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="4" y="0" width="2" height="2"/><rect x="8" y="2" width="2" height="2"/><rect x="2" y="4" width="2" height="2"/><rect x="6" y="6" width="2" height="2"/><rect x="0" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame nav-item__icon-frame--final" viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="0" width="2" height="2"/><rect x="8" y="0" width="2" height="2"/><rect x="4" y="4" width="2" height="2"/><rect x="0" y="8" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/></svg>
      </span><span class="nav-item__text">Services</span></a>
    <a class="nav-item" href="#"><span class="nav-item__bg"></span><span class="nav-item__line"></span>
      <span class="nav-item__icon">
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="0" width="2" height="2"/><rect x="4" y="2" width="2" height="2"/><rect x="8" y="4" width="2" height="2"/><rect x="2" y="6" width="2" height="2"/><rect x="6" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="2" y="0" width="2" height="2"/><rect x="6" y="2" width="2" height="2"/><rect x="0" y="4" width="2" height="2"/><rect x="4" y="6" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="4" y="0" width="2" height="2"/><rect x="8" y="2" width="2" height="2"/><rect x="2" y="4" width="2" height="2"/><rect x="6" y="6" width="2" height="2"/><rect x="0" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame nav-item__icon-frame--final" viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="0" width="2" height="2"/><rect x="8" y="0" width="2" height="2"/><rect x="4" y="4" width="2" height="2"/><rect x="0" y="8" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/></svg>
      </span><span class="nav-item__text">About</span></a>
    <a class="nav-item" href="#"><span class="nav-item__bg"></span><span class="nav-item__line"></span>
      <span class="nav-item__icon">
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="0" width="2" height="2"/><rect x="4" y="2" width="2" height="2"/><rect x="8" y="4" width="2" height="2"/><rect x="2" y="6" width="2" height="2"/><rect x="6" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="2" y="0" width="2" height="2"/><rect x="6" y="2" width="2" height="2"/><rect x="0" y="4" width="2" height="2"/><rect x="4" y="6" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame" viewBox="0 0 10 10" fill="currentColor"><rect x="4" y="0" width="2" height="2"/><rect x="8" y="2" width="2" height="2"/><rect x="2" y="4" width="2" height="2"/><rect x="6" y="6" width="2" height="2"/><rect x="0" y="8" width="2" height="2"/></svg>
        <svg class="nav-item__icon-frame nav-item__icon-frame--final" viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="0" width="2" height="2"/><rect x="8" y="0" width="2" height="2"/><rect x="4" y="4" width="2" height="2"/><rect x="0" y="8" width="2" height="2"/><rect x="8" y="8" width="2" height="2"/></svg>
      </span><span class="nav-item__text">Contact</span></a>
  </div>
</div>
```

## 2. HTML — Hero, buttons, contact cards. Buttons and cards need no JS: hover is CSS.

```html
<section class="section section--hero">
  <div>
    <p class="section__eyebrow">[ Micro-interactions ]</p>
    <h1 class="hero__title">Open the pill menu.<br>Hover the buttons.</h1>
  </div>
</section>

<section class="section">
  <h2 class="section__title">Buttons: fill + text swap + arrow hand-off</h2>
  <div class="button-row">
    <a class="button" href="#"><span class="button__fill"></span>
      <span class="button__inner"><span class="button__text">View case</span><svg class="button__arrow" viewBox="0 0 7 7"><path d="M0 0h7v7H5V3.4L1.4 7 0 5.6 3.6 2H0z" fill="currentColor"/></svg></span>
      <span class="button__hover"><span class="button__text">View case</span><svg class="button__arrow" viewBox="0 0 7 7"><path d="M0 0h7v7H5V3.4L1.4 7 0 5.6 3.6 2H0z" fill="currentColor"/></svg></span>
    </a>
    <a class="button" href="#"><span class="button__fill"></span>
      <span class="button__inner"><span class="button__text">Our pitchdeck</span></span>
      <span class="button__hover"><span class="button__text">Our pitchdeck</span></span>
    </a>
    <a class="button" href="#"><span class="button__fill"></span>
      <span class="button__inner"><span class="button__text">Schedule a call</span><svg class="button__arrow" viewBox="0 0 7 7"><path d="M0 0h7v7H5V3.4L1.4 7 0 5.6 3.6 2H0z" fill="currentColor"/></svg></span>
      <span class="button__hover"><span class="button__text">Schedule a call</span><svg class="button__arrow" viewBox="0 0 7 7"><path d="M0 0h7v7H5V3.4L1.4 7 0 5.6 3.6 2H0z" fill="currentColor"/></svg></span>
    </a>
  </div>
</section>

<section class="section">
  <h2 class="section__title">Contact card: fill sweeps in, label swaps side</h2>
  <div class="button-row">
    <a class="contact-card" href="#"><span class="contact-card__bg"></span><span class="contact-card__fill"></span>
      <span class="contact-card__label-hover">Get in touch</span>
      <span class="contact-card__avatar"></span><span class="contact-card__label">Get in touch</span>
    </a>
    <a class="contact-card" href="#"><span class="contact-card__bg"></span><span class="contact-card__fill"></span>
      <span class="contact-card__label-hover">+00 00 000 0000</span>
      <span class="contact-card__avatar contact-card__avatar--green"></span><span class="contact-card__label">+00 00 000 0000</span>
    </a>
  </div>
</section>
<div class="spacer"></div>
```

## 3. CSS — Page base + sections.

```css
*, *::before, *::after { box-sizing: border-box; }   /* Webflow default; keeps min-height/aspect-ratio maths sane */
body { margin: 0; background-color: #111111; color: #f1efe8; font-family: system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.4; }
.section { padding: 120px 40px; }
.section--hero { min-height: 100vh; display: flex; align-items: flex-end; padding-bottom: 8vh; }
.section__eyebrow { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; color: rgba(241, 239, 232, 0.55); margin: 0 0 24px 0; }
.section__title { font-size: 48px; line-height: 1.05; letter-spacing: -0.02em; font-weight: 500; margin: 0 0 32px 0; }
.hero__title { font-size: 80px; line-height: 0.98; letter-spacing: -0.03em; font-weight: 500; margin: 0; }
.button-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.spacer { height: 40vh; }
```

## 4. CSS — Nav pill + nav items. Hidden layers (line, text clip, icon frames) are revealed by the GSAP open timeline; item hover is CSS.

```css
.menu-blur { position: fixed; inset: 0; z-index: 39; background-color: rgba(0, 0, 0, 0.4); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); opacity: 0; pointer-events: none; }
.nav-pill { position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 40; width: calc(100vw - 32px); max-width: 438px; border-radius: 6px; overflow: hidden; backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); }
.nav-pill__bg { position: absolute; inset: 0; background-color: #1f1f1f; opacity: 0.6; }
.nav-pill__bar { position: relative; display: flex; align-items: center; justify-content: space-between; height: 50px; padding: 0 13px 0 9px; cursor: pointer; }
.nav-pill__logo { width: 22px; height: 22px; display: block; }
.nav-pill__message { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; text-transform: uppercase; }
.nav-pill__burger { display: flex; flex-direction: column; gap: 3px; padding: 12px 7px; background: none; border: 0; cursor: pointer; }
.nav-pill__burger:focus-visible { outline: 2px solid #ff4d2e; outline-offset: 2px; }
.nav-pill__burger-line { display: block; height: 2px; width: 16px; background-color: currentColor; }
.nav-pill__items { height: 0; overflow: hidden; position: relative; }
.nav-item { position: relative; display: flex; align-items: center; height: 50px; width: 100%; padding-left: 43px; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; text-transform: uppercase; color: inherit; text-decoration: none; }
.nav-item__bg { position: absolute; inset: 0; background-color: rgba(255, 255, 255, 0.1); opacity: 0; transition: opacity 0.25s ease; }
.nav-item:hover .nav-item__bg, .nav-item:focus-visible .nav-item__bg { opacity: 1; }
.nav-item__line { position: absolute; left: 0; right: 0; top: 0; height: 1px; background-color: currentColor; opacity: 0.1; transform: scaleX(0); transform-origin: left center; }
.nav-item__icon { position: absolute; left: 12px; width: 10px; height: 10px; }
.nav-item__icon-frame { position: absolute; inset: 0; width: 10px; height: 10px; opacity: 0; }
.nav-item__icon-frame--final { opacity: 1; }
.nav-item__text { position: relative; clip-path: inset(0 0 100% 0); }
```

## 5. CSS — Button and contact card. Hover is pure CSS: fill, text swap, diagonal arrow hand-off with transition-delay.

```css
.button { position: relative; display: inline-flex; border-radius: 6px; white-space: nowrap; color: inherit; text-decoration: none; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; text-transform: uppercase; }
.button__fill { position: absolute; inset: 0; border-radius: 6px; background-color: #f1efe8; opacity: 0; transition: opacity 0.35s ease; }
.button__inner, .button__hover { display: flex; align-items: center; justify-content: center; gap: 10px; height: 50px; padding: 0 16px; border-radius: 6px; }
.button__inner { position: relative; border: 1px solid rgba(241, 239, 232, 0.2); }
.button__hover { position: absolute; inset: 0; color: #111111; }
.button__text { transition: opacity 0.2s ease; }
.button__hover .button__text { opacity: 0; transition-delay: 0.1s; }
.button__arrow { width: 7px; height: 7px; transition: transform 0.25s ease; }
.button__inner .button__arrow { transform-origin: top right; }
.button__hover .button__arrow { transform-origin: bottom left; transform: scale(0); transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) 0.12s; }
.button:hover .button__fill, .button:focus-visible .button__fill { opacity: 1; }
.button:hover .button__inner .button__text, .button:focus-visible .button__inner .button__text { opacity: 0; }
.button:hover .button__hover .button__text, .button:focus-visible .button__hover .button__text { opacity: 1; }
.button:hover .button__inner .button__arrow, .button:focus-visible .button__inner .button__arrow { transform: scale(0); }
.button:hover .button__hover .button__arrow, .button:focus-visible .button__hover .button__arrow { transform: scale(1); }
.button:focus-visible { outline: 2px solid #ff4d2e; outline-offset: 2px; }
.contact-card { position: relative; display: inline-flex; align-items: center; gap: 20px; height: 50px; padding: 0 32px 0 11px; border-radius: 6px; overflow: hidden; white-space: nowrap; color: inherit; text-decoration: none; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; text-transform: uppercase; }
.contact-card__bg { position: absolute; inset: 0; background-color: #1f1f1f; }
.contact-card__fill { position: absolute; inset: 0; background-color: #f1efe8; opacity: 0; transition: opacity 0.35s ease; }
.contact-card__avatar { position: relative; z-index: 2; width: 28px; height: 28px; border-radius: 3px; background-color: #7a5a45; background-image: repeating-linear-gradient(135deg, rgba(255,255,255,0.06) 0 6px, transparent 6px 14px); transition: transform 0.35s ease; }
.contact-card__avatar--green { background-color: #4f6b52; }
.contact-card__label { position: relative; z-index: 2; transition: transform 0.25s ease, opacity 0.25s ease; }
.contact-card__label-hover { position: absolute; right: 32px; z-index: 2; color: #111111; opacity: 0; transform: translateX(-12px); transition: transform 0.35s ease 0.1s, opacity 0.35s ease 0.1s; }
.contact-card:hover .contact-card__fill, .contact-card:focus-visible .contact-card__fill { opacity: 1; }
.contact-card:hover .contact-card__label, .contact-card:focus-visible .contact-card__label { transform: translateX(16px); opacity: 0; }
.contact-card:hover .contact-card__avatar, .contact-card:focus-visible .contact-card__avatar { transform: translateX(6px); }
.contact-card:hover .contact-card__label-hover, .contact-card:focus-visible .contact-card__label-hover { transform: translateX(0); opacity: 1; }
.contact-card:focus-visible { outline: 2px solid #ff4d2e; outline-offset: 2px; }
```

## 6. JS — Menu open/close only (buttons and cards are CSS). Split into a convertible timeline and an Embed-only one.

```js
gsap.registerPlugin(ScrambleTextPlugin);
const items = gsap.utils.toArray(".nav-item");

/* [FLOWBOARD: CONVERTIBLE] Basic open timeline: blur opacity, burger → X, panel height, line scaleX with stagger.
 * (height:"auto" becomes a fixed px height in Interactions; measure the open panel.) */
const openTl = gsap.timeline({
  paused: true, defaults: { ease: "power3.out" },
  onStart: () => gsap.set(".menu-blur", { pointerEvents: "auto" }),
  onReverseComplete: () => gsap.set(".menu-blur", { pointerEvents: "none" })
});
openTl.to(".menu-blur", { opacity: 1, duration: 0.4 }, 0)
      .to(".nav-pill__items", { height: "auto", duration: 0.55, ease: "power3.inOut" }, 0)
      .to(".nav-pill__burger-line--top", { y: 5, rotate: 45, duration: 0.3 }, 0)
      .to(".nav-pill__burger-line--bottom", { y: -5, rotate: -45, duration: 0.3 }, 0)
      .to(".nav-pill__burger-line--middle", { scaleX: 0, duration: 0.2 }, 0)
      .to(".nav-item__line", { scaleX: 1, duration: 0.6, stagger: 0.06 }, 0.1);

/* [FLOWBOARD: EMBED ONLY] clip-path text reveal, ScrambleText message, stepped icon-frame cycling.
 * Runs in lockstep with openTl via the same play()/reverse() calls. */
const extraTl = gsap.timeline({ paused: true, defaults: { ease: "power3.out" } });
extraTl.to(".nav-pill__message", { duration: 0.5, scrambleText: { text: "[ close ]", chars: "[]/\\|-_=+*#", speed: 0.6, tweenLength: false } }, 0)
       .to(".nav-item__text", { clipPath: "inset(0 0 0% 0)", duration: 0.5, stagger: 0.06 }, 0.15);
items.forEach((item, i) => {
  const frames = item.querySelectorAll(".nav-item__icon-frame");
  frames.forEach((f, k) => extraTl.set(frames, { opacity: 0 }, 0.15 + i * 0.06 + k * 0.07).set(f, { opacity: 1 }, 0.15 + i * 0.06 + k * 0.07));
});

let open = false;
document.querySelector(".nav-pill__bar").addEventListener("click", () => {
  open = !open;
  if (open) { openTl.play(); extraTl.play(); } else { openTl.reverse(); extraTl.reverse(); }
});
document.querySelector(".menu-blur").addEventListener("click", () => { open = false; openTl.reverse(); extraTl.reverse(); });
```
