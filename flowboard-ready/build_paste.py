"""Generate paste.md for each flowboard-ready folder from its index.html so the two never drift.
Splits on marker comments:  /* @snippet CSS: note */   <!-- @snippet HTML: note -->   // @snippet JS: note"""
import re, os, glob
ROOT = os.path.dirname(os.path.abspath(__file__))
def split(region, pattern):
    parts = re.split(pattern, region)
    out = []
    # parts: [pre, note1, body1, note2, body2 ...]
    for i in range(1, len(parts), 2):
        out.append((parts[i].strip(), parts[i + 1].strip('\n')))
    return out
def dedent(block):
    lines = block.split('\n')
    ind = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    return '\n'.join(l[ind:] if l.strip() else '' for l in lines).strip('\n')
for folder in sorted(glob.glob(ROOT + '/0*/')):
    html = open(folder + 'index.html').read()
    title = re.search(r'<title>(.*?)</title>', html).group(1).replace(' (Flowboard-ready)', '')
    css = re.search(r'<style>(.*?)</style>', html, re.S).group(1)
    body = re.search(r'<body>(.*?)<script src', html, re.S).group(1)
    js = re.search(r'<script>\n(.*?)</script>', html, re.S).group(1)
    scripts = re.findall(r'<script src="([^"]+)"></script>', html)
    css_snips = split(css, r'/\* @snippet CSS: (.*?) \*/\n')
    html_snips = split(body, r'<!-- @snippet HTML: (.*?) -->\n')
    js_snips = split(js, r'// @snippet JS: (.*?)\n')
    md = [f'# {title} — Flowboard paste snippets\n',
          'Paste in this order: HTML, then CSS, then JS. Each fenced block is one paste. The GSAP scripts below go in '
          '**Project Settings → Custom Code → Footer** (before `</body>`), above the JS Embed:\n',
          '```html\n' + '\n'.join(f'<script src="{s}"></script>' for s in scripts) + '\n```\n']
    n = 0
    for label, snips in (('HTML', html_snips), ('CSS', css_snips), ('JS', js_snips)):
        for note, code in snips:
            n += 1
            lang = {'HTML': 'html', 'CSS': 'css', 'JS': 'js'}[label]
            md.append(f'## {n}. {label} — {note}\n\n```{lang}\n{dedent(code)}\n```\n')
    open(folder + 'paste.md', 'w').write('\n'.join(md))
    sizes = [len(dedent(c)) for _, c in html_snips + css_snips + js_snips]
    print(os.path.basename(folder.rstrip('/')), 'snippets:', n, 'max chars:', max(sizes))
