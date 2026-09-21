# 05 · Preloader + page transitions — Flowboard paste snippets

Paste in this order: HTML, then CSS, then JS. Each fenced block is one paste. The GSAP scripts below go in **Project Settings → Custom Code → Footer** (before `</body>`), above the JS Embed:

```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/SplitText.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/ScrambleTextPlugin.min.js"></script>
```

## 1. HTML — Preloader, header, page container, transition layers.

```html
<div class="preloader"><span><span class="preloader__count">0</span>%</span></div>

<header class="site-header">
  <span class="site-header__title">Home</span>
  <nav class="site-header__nav">
    <a href="#home" class="site-header__link is-active" data-route="home">Home</a>
    <a href="#work" class="site-header__link" data-route="work">Work</a>
    <a href="#about" class="site-header__link" data-route="about">About</a>
  </nav>
</header>

<main class="page-container"></main>

<div class="transition-overlay"></div>
<div class="transition-counter"><span><span class="transition-counter__value">0</span>%</span></div>
```

## 2. HTML — Page templates — stand-ins for the server pages Swup would fetch. In Webflow these are real pages; see README.

```html
<template data-page="home">
  <div class="page" data-title="Home">
    <p class="page__eyebrow">[ Home ]</p>
    <h1 class="page__title">A fake home page with lorem ipsum.</h1>
    <p class="page__lead">Click the nav. The overlay covers the page, a counter runs, the content swaps underneath, and the new page's reveals play on enter.</p>
    <div class="page__image page__image--blue"></div>
  </div>
</template>
<template data-page="work">
  <div class="page" data-title="Work">
    <p class="page__eyebrow">[ Work ]</p>
    <h1 class="page__title">Work that placeholder works.</h1>
    <p class="page__lead">Every "page" is a template in this file. In production, Swup fetches the real HTML and swaps a container; the hooks are the same.</p>
    <div class="page__image page__image--green"></div>
  </div>
</template>
<template data-page="about">
  <div class="page" data-title="About">
    <p class="page__eyebrow">[ About ]</p>
    <h1 class="page__title">About nobody in particular.</h1>
    <p class="page__lead">Use the browser back button: popstate routes through the same transition.</p>
    <div class="page__image page__image--purple"></div>
  </div>
</template>
```

## 3. CSS — Page base, preloader, transition overlay + counter.

```css
*, *::before, *::after { box-sizing: border-box; }   /* Webflow default; keeps min-height/aspect-ratio maths sane */
body { margin: 0; background-color: #111111; color: #f1efe8; font-family: system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.4; }
.preloader { position: fixed; inset: 0; z-index: 100; display: grid; place-items: center; background-color: #000000; color: #ffffff; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11px; text-transform: uppercase; }
.transition-overlay { position: fixed; inset: 0; z-index: 80; background-color: #111111; opacity: 0; pointer-events: none; }
.transition-counter { position: fixed; inset: 0; z-index: 81; display: grid; place-items: center; pointer-events: none; opacity: 0; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; }
```

## 4. CSS — Persistent header + page content.

```css
.site-header { position: fixed; top: 16px; left: 50%; transform: translateX(-50%); z-index: 90; display: flex; align-items: center; gap: 20px; padding: 10px 14px; border-radius: 6px; background-color: rgba(31, 31, 31, 0.75); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); }
.site-header__title { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; min-width: 12ch; }
.site-header__nav { display: flex; gap: 14px; }
.site-header__link { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; color: inherit; text-decoration: none; opacity: 0.6; }
.site-header__link:hover { opacity: 0.85; }
.site-header__link:focus-visible { outline: 2px solid #ff4d2e; outline-offset: 2px; }
.site-header__link.is-active { opacity: 1; }
.page-container { padding: 0 40px; }
.page { min-height: 120vh; padding-top: 140px; }
.page__eyebrow { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 12px; text-transform: uppercase; color: rgba(241, 239, 232, 0.55); margin: 0 0 24px 0; }
.page__title { font-size: 80px; line-height: 0.98; letter-spacing: -0.03em; font-weight: 500; margin: 0; max-width: 14ch; opacity: 0; }
.page__lead { font-size: 18px; max-width: 40ch; color: rgba(241, 239, 232, 0.55); margin: 24px 0 0 0; }
.page__image { aspect-ratio: 16 / 9; margin-top: 48px; border-radius: 6px; opacity: 0; background-color: #3a3a3a; background-image: repeating-linear-gradient(135deg, rgba(255,255,255,0.06) 0 6px, transparent 6px 14px); }
.page__image--blue { background-color: #4a5d73; } .page__image--green { background-color: #4f6b52; } .page__image--purple { background-color: #6b4f6b; }
```

## 5. JS — Preloader counter, page enter, out→swap→in transition, routing. Mostly Embed; overlay fades are convertible.

```js
gsap.registerPlugin(SplitText, ScrambleTextPlugin);
const page = document.querySelector(".page-container");
const headerTitle = document.querySelector(".site-header__title");
const overlay = document.querySelector(".transition-overlay");
const counterWrap = document.querySelector(".transition-counter");
const counterEl = document.querySelector(".transition-counter__value");

/* [FLOWBOARD: EMBED ONLY] Number counter: tweens an object and writes the snapped value into the DOM. */
function countTo(el, from, to, duration, ease = "power2.inOut") {
  const o = { n: from };
  return gsap.to(o, { n: to, duration, ease, snap: { n: 1 }, onUpdate: () => (el.textContent = o.n) });
}

/* [FLOWBOARD: CONVERTIBLE] Preloader fade-out is a "page load" opacity tween. [EMBED] the counter it wraps. */
const preloader = document.querySelector(".preloader");
const preloaderCount = document.querySelector(".preloader__count");
const loaderTl = gsap.timeline();
loaderTl.add(countTo(preloaderCount, 0, 80, 0.9));
window.addEventListener("load", () => {
  loaderTl.add(countTo(preloaderCount, 80, 100, 0.35))
          .to(preloader, { opacity: 0, duration: 0.5, ease: "power2.inOut" })
          .set(preloader, { display: "none" })
          .add(() => enterPage(), "-=0.3");
});

/* [FLOWBOARD: EMBED ONLY] Render a template into the container (Swup does this with fetched HTML). */
function render(route) {
  const tpl = document.querySelector(`template[data-page="${route}"]`);
  page.replaceChildren(tpl.content.cloneNode(true));
  document.querySelectorAll(".site-header__link").forEach(a => a.classList.toggle("is-active", a.dataset.route === route));
}

/* [FLOWBOARD: EMBED ONLY] Page-enter: SplitText lines. [CONVERTIBLE] the image fade/slide inside it is a basic tween. */
function enterPage() {
  const title = page.querySelector(".page__title");
  const split = SplitText.create(title, { type: "lines", mask: "lines" });
  const tl = gsap.timeline();
  tl.set(title, { opacity: 1 })
    .from(split.lines, { yPercent: 110, duration: 0.9, ease: "power3.out", stagger: 0.08 })
    .fromTo(page.querySelector(".page__image"), { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.9, ease: "power2.out" }, "-=0.5");
  return tl;
}

/* [FLOWBOARD: CONVERTIBLE] overlay + counter opacity tweens (page-load / link-click IX).
 * [EMBED ONLY] the counter, the content swap, the header ScrambleText and the routing. */
let busy = false;
async function goTo(route, pushHistory = true) {
  if (busy) return;
  busy = true;
  if (pushHistory) history.pushState({ route }, "", "#" + route);
  const out = gsap.timeline();
  out.to(overlay, { opacity: 1, duration: 0.45, ease: "power2.inOut" })
     .to(counterWrap, { opacity: 1, duration: 0.2 }, "<")
     .add(countTo(counterEl, 0, 100, 0.7), "<0.1");
  await out;
  window.scrollTo(0, 0);
  render(route);
  gsap.to(headerTitle, { duration: 0.6, scrambleText: { text: page.querySelector(".page").dataset.title, chars: "[]/\\|-_=+*#", speed: 0.6, tweenLength: false } });
  const inTl = gsap.timeline();
  inTl.to(counterWrap, { opacity: 0, duration: 0.2 })
      .to(overlay, { opacity: 0, duration: 0.5, ease: "power2.inOut" }, "<")
      .add(enterPage(), "-=0.25");
  await inTl;
  busy = false;
}
document.addEventListener("click", e => {
  const link = e.target.closest(".site-header__link");
  if (!link) return;
  e.preventDefault();
  if (!link.classList.contains("is-active")) goTo(link.dataset.route);
});
window.addEventListener("popstate", e => goTo((e.state && e.state.route) || "home", false));
const initial = location.hash.slice(1) || "home";
render(document.querySelector(`template[data-page="${initial}"]`) ? initial : "home");
history.replaceState({ route: initial }, "", "#" + initial);
```
