"""Build preview/index.html from sections/*.html.
Rewrites placehold.co placeholders to inline SVG data URIs so the preview has no external image deps."""
import re, glob, os, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = sorted(glob.glob(os.path.join(ROOT, 'sections', '*.html')))

PLACEHOLDER = re.compile(r'https://placehold\.co/(\d+)x(\d+)/([0-9a-fA-F]{6})/([0-9a-fA-F]{6})\?text=([^"\']*)')

def svg_uri(m):
    w, h, bg, fg, text = m.groups()
    w, h = int(w), int(h)
    label = urllib.parse.unquote_plus(text)
    size = max(12, min(w, h) // 6)
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
           f"<rect width='100%' height='100%' fill='#{bg}'/>"
           f"<rect x='0.5' y='0.5' width='{w-1}' height='{h-1}' fill='none' stroke='#{fg}' stroke-opacity='0.35'/>"
           f"<text x='50%' y='50%' fill='#{fg}' font-family='Helvetica,Arial,sans-serif' font-size='{size}' "
           f"text-anchor='middle' dominant-baseline='middle'>{label}</text></svg>")
    return 'data:image/svg+xml;charset=utf-8,' + urllib.parse.quote(svg, safe="'=:/ ,.")

parts = []
for f in files:
    src = open(f, encoding='utf-8').read()
    src = PLACEHOLDER.sub(svg_uri, src)
    parts.append(f"<!-- ===== {os.path.basename(f)} ===== -->\n{src}")

head = """<title>Playmaker 2026 Homepage</title>
<meta name="description" content="Static preview of the Figma → Webflow build. Placeholder art; swap for exported assets.">
<style>
  body { margin: 0; background: #101010; color: #fff; }
  .preview_note { position: fixed; right: 1rem; bottom: 1rem; z-index: 50; padding: 0.5rem 0.75rem; border: 1px solid rgba(255,255,255,0.2); border-radius: 999px; background: rgba(16,16,16,0.85); color: rgba(255,255,255,0.6); font: 12px/1.4 "Helvetica Neue", Arial, sans-serif; letter-spacing: 0.02em; backdrop-filter: blur(6px); }
</style>
<div class="page-wrapper">
"""
tail = """
</div>
<p class="preview_note">Preview · placeholder art · Euclid Circular A falls back to system sans</p>
"""
out = os.path.join(ROOT, 'preview', 'index.html')
open(out, 'w', encoding='utf-8').write(head + "\n".join(parts) + tail)
print(out, os.path.getsize(out), 'bytes')
