#!/usr/bin/env python3
"""Compose every collage as a staggered, gutter-consistent arrangement in which each
photo or clip keeps its exact aspect ratio (nothing is ever cropped).

    python3 tools/layout.py

How a collage is built (per project, and the hero):
  • columns: 2 for up to five items (a wide lead column and a narrower one), 3 for six or
    more; the first item is the lead and spans the wide column (or two columns when there
    are six or more), so the video or key photo reads first;
  • each following item goes to the column that currently ends highest (masonry), with the
    columns starting at different heights and items alternating between full and slightly
    narrower widths, which gives the deliberate scatter of the brief without holes;
  • the result is written as absolute positions (left / top / width in % of the collage
    width) into the CSS between the LAYOUTS markers, and each slot gets
    style="aspect-ratio:W/H" from its own file so its height follows its media.
tools/layouts.json records the generated slots; set "manual": true on a key and edit its
slots to take over by hand. Also inserts the sound / play buttons.
Run after build_images.py, and after editing layouts.json.
"""
import json, os, random, re, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
GUT = 3.4                     # gutter, % of collage width
html = open("index.html").read()
LAY = "tools/layouts.json"
layouts = json.load(open(LAY)) if os.path.exists(LAY) else {}

def aspect(item):
    m = re.search(r'<video[^>]*poster="([^"]+)"', item) or re.search(r'<img src="([^"]+)"', item)
    path = m.group(1)
    if not os.path.exists(path):
        return 1.5, "3/2"
    w, h = Image.open(path).size
    return w / h, f"{w}/{h}"

# air: gap under a piece (fraction of the narrower width); bite: the occasional light overlap;
# p_bite: share of pieces that overlap; hpad: minimum side-by-side margin (% of width)
DESKTOP = dict(widths=(14, 17, 21, 25, 30, 34), bleed=5.0, first=28, target=78, air=(0.01, 0.08), bite=(0.10, 0.30),
               p_bite=0.72, hpad=-5.0, min_vis=0.62, cover=0.70)
MOBILE  = dict(widths=(40, 46, 52, 60), bleed=6.0, first=58, target=250, air=(0.01, 0.06), bite=(0.08, 0.24),
               p_bite=0.65, hpad=-6.0, min_vis=0.62, cover=0.70)

def scatter(aspects, seed=58, tries=160, widths=DESKTOP["widths"], bleed=2.0, first=30, air=(0.12, 0.34),
            bite=(0.05, 0.12), p_bite=0.3, hpad=2.4, min_vis=0.9, **_):
    """Dense, messy collage for the hero after Reference.png (the user asked on 6 Oct 2026 for
    all fifteen projects, "more crowded, not organized"): pieces of different sizes piled on
    one another, most overlapping a neighbour, some bleeding off the sides, small gaps only.
    `min_vis` keeps enough of every piece visible to read it.

    Each piece gets its own random width and its own spacing (a gap, or with probability
    p_bite a small overlap) *before* positions are tried, so choosing the highest free spot
    cannot quietly favour the tightest spacing. Pieces closer than `hpad` side by side count
    as stacked, so nothing sits flush against a neighbour. Seeds live in tools/layouts.json;
    `--reseed` searches for the most balanced arrangement."""
    rnd = random.Random(seed)
    SX, SY = 6, 4
    placed = []
    for i, a in enumerate(aspects):
        w = first if i == 0 else widths[rnd.randrange(len(widths))]
        h = w / a
        frac = rnd.uniform(*bite) if rnd.random() < p_bite else -rnd.uniform(*air)   # >0 overlap, <0 air
        best = fallback = None
        for _ in range(tries):
            x = rnd.uniform(-bleed, 100 - w + bleed)
            y = 0.0
            for (px, py, pw, ph, _p) in placed:
                if x < px + pw + hpad and px < x + w + hpad:
                    y = max(y, py + ph - min(w, pw) * frac)
            worst = 1.0
            for (px, py, pw, ph, pts) in placed:
                if x < px + pw and px < x + w and y < py + ph and py < y + h:
                    vis = sum(1 for (qx, qy, hid) in pts if not hid and not (x <= qx <= x + w and y <= qy <= y + h))
                    worst = min(worst, vis / len(pts))
            score = y + rnd.uniform(0, 2.0)
            if worst >= min_vis:
                if best is None or score < best[0]:
                    best = (score, x, y)
            elif fallback is None or worst > fallback[0]:
                fallback = (worst, x, y)
        _, x, y = best or fallback
        for (_x, _y, _w, _h, pts) in placed:
            for q in pts:
                if not q[2] and x <= q[0] <= x + w and y <= q[1] <= y + h:
                    q[2] = True
        pts = [[x + (gx + .5) * w / SX, y + (gy + .5) * h / SY, False] for gx in range(SX) for gy in range(SY)]
        placed.append((x, y, w, h, pts))
    return [(x, y, w) for (x, y, w, h, _p) in placed], [sum(not q[2] for q in p) / len(p) for (*_r, p) in placed]

def evenness(slots, aspects, target, cover=None):
    """How good an arrangement looks, higher is better: coverage close to `cover` (so there is
    air but no big holes), every quarter of the collage used, picture mass centred left to
    right, and a height close to `target` (in % of width)."""
    boxes = [(x, y, w, w / a) for (x, y, w), a in zip(slots, aspects)]
    bottom = max(y + h for _, y, _, h in boxes)
    GX, GY = 20, 12
    grid = [[any(x <= (gx + .5) * 100 / GX <= x + w and y <= (gy + .5) * bottom / GY <= y + h for x, y, w, h in boxes)
             for gy in range(GY)] for gx in range(GX)]
    cov = sum(map(sum, grid)) / (GX * GY)
    quads = [sum(grid[gx][gy] for gx in range(qx * GX // 2, (qx + 1) * GX // 2) for gy in range(qy * GY // 2, (qy + 1) * GY // 2)) / (GX * GY / 4)
             for qx in (0, 1) for qy in (0, 1)]
    area = sum(w * h for _, _, w, h in boxes)
    cx = sum((x + w / 2) * w * h for x, _, w, h in boxes) / area
    score = (cov if cover is None else 1 - abs(cov - cover) * 1.6)
    inner = [grid[gx][gy] for gx in range(2, GX - 2) for gy in range(1, GY - 1)]
    score -= max(0, 0.82 - sum(inner) / len(inner)) * 3.0          # no holes in the middle of the pile
    score -= max(0, 0.55 - min(quads)) * 3.0 + abs(cx - 50) / 60 + abs(bottom - target) / (target * 3.5)
    return score

def best_seed(aspects, params, seeds=range(1, 241)):
    def score(sd):
        slots, vis = scatter(aspects, seed=sd, **params)
        return evenness(slots, aspects, params["target"], params.get("cover")) - max(0, 0.8 - min(vis)) * 4   # nobody buried
    return max(seeds, key=score)

def compose(aspects, hero=False):
    n = len(aspects)
    if n == 1:
        return [(0, 0, 66)], None
    if n <= 5:
        cols = [(0, 60), (60 + GUT, 100 - 60 - GUT)]
        starts = [0, 7]; lead_span = 1
    else:
        w1, w2 = 33, 29.2
        cols = [(0, w1), (w1 + GUT, w2), (w1 + GUT + w2 + GUT, 100 - (w1 + GUT + w2 + GUT))]
        starts = [0, 6, 3]; lead_span = 2
    bottoms = list(starts)
    slots = []
    for i, a in enumerate(aspects):
        if i == 0 and lead_span:
            left = cols[0][0]; width = (cols[lead_span - 1][0] + cols[lead_span - 1][1]) - left
            top = 0; h = width / a
            for c in range(lead_span): bottoms[c] = top + h + GUT
            slots.append((left, top, width)); continue
        c = min(range(len(cols)), key=lambda k: (bottoms[k], k))
        left, cw = cols[c]
        # alternate full / slightly narrower widths for a hand-placed feel
        k = sum(1 for s in slots if abs(s[0] - left) < 0.01 or (left < s[0] < left + cw))
        width = cw if (k % 2 == 0 or n <= 3) else cw * 0.86
        if width != cw and (c == len(cols) - 1 or (i % 2)):
            left = left + (cw - width)          # push narrower items to the column's far edge sometimes
        top = bottoms[c]
        bottoms[c] = top + width / a + GUT
        slots.append((left, top, width))
    return slots, None

def solve(slots, aspects):
    """Final guard: keep DOM order, resolve any overlap by pushing down; returns (bottom, positions%)."""
    placed = []
    for (left, top, width), a in zip(slots, aspects):
        h = width / a
        for (l2, t2, w2, h2) in placed:
            if left < l2 + w2 and l2 < left + width:
                top = max(top, t2 + h2 + GUT)
        placed.append((left, top, width, h))
    bottom = max(t + h for (_, t, _, h) in placed)
    return bottom, [(l, t / bottom * 100, w) for (l, t, w, h) in placed]

css = []
css_m = []
RESEED = "--reseed" in sys.argv
def rebuild(collage_html, key, class_name, hero=False):
    open_tag_m = re.match(r'<(nav|div) class="collage[^"]*"[^>]*>', collage_html)
    tag = open_tag_m.group(1); open_tag = open_tag_m.group(0)
    inner = collage_html[len(open_tag):-len(f"</{tag}>")]
    inner = re.sub(r'\s*<div class="row"[^>]*>|\s*</div>', "", inner)      # unwrap any row markup
    items = [m.group(0) for m in re.finditer(r'<(figure|a) class="ph[^"]*"[^>]*>.*?</\1>', inner, re.S)]
    asp = [aspect(it) for it in items]
    spec = layouts.setdefault(key, {})
    A = [a for a, _ in asp]
    if hero:
        if RESEED or "seed" not in spec:
            spec["seed"], spec["seed_m"] = best_seed(A, DESKTOP), best_seed(A, MOBILE)
        slots, _ = scatter(A, seed=spec["seed"], **DESKTOP)
        m_slots, _ = scatter(A, seed=spec["seed_m"], **MOBILE)
        spec["slots"] = [{"left": round(l, 2), "top": round(t, 2), "width": round(w, 2)} for l, t, w in slots]
        spec["slots_m"] = [{"left": round(l, 2), "top": round(t, 2), "width": round(w, 2)} for l, t, w in m_slots]
        spec["manual"] = False
        def place(sl):                         # keep the deliberate overlaps — no push-down pass
            b = max(t + w / a for (_, t, w), a in zip(sl, A))
            return b, [(l, t / b * 100, w) for (l, t, w) in sl]
        bottom, pos = place(slots)
        bm, pos_m = place(m_slots)
        vis_d = scatter(A, seed=spec["seed"], **DESKTOP)[1]; vis_m = scatter(A, seed=spec["seed_m"], **MOBILE)[1]
        print(f"hero: least-visible picture {min(vis_d):.0%} on desktop, {min(vis_m):.0%} on phones")
        css_m.append(f"  .{class_name}{{columns:auto;aspect-ratio:100/{bm:.2f}}}")
        css_m.append(f"  .{class_name}>.ph{{position:absolute;margin:0}}")
        for i, (l, t, w) in enumerate(pos_m, 1):
            css_m.append(f"  .{class_name} .ph:nth-child({i}){{left:{l:.2f}%;top:{t:.2f}%;width:{w:.2f}%}}")
    else:
        if spec.get("manual") and len(spec.get("slots", [])) == len(items):
            slots = [(s["left"], s["top"], s["width"]) for s in spec["slots"]]
        else:
            slots, _ = compose(A, hero)
            spec["slots"] = [{"left": round(l, 2), "top": round(t, 2), "width": round(w, 2)} for l, t, w in slots]
            spec["manual"] = False
        bottom, pos = solve(slots, A)
    out = []
    for it, (a, frac) in zip(items, asp):
        head_end = it.index(">")
        head = re.sub(r'\s*style="[^"]*"', "", it[:head_end]) + f' style="aspect-ratio:{frac}"'
        body = it[head_end:]
        if "<video" in body and 'class="vb' not in body:
            if 'data-autoplay="off"' in body:
                btn = '<button class="vb vb--play" type="button" aria-label="Play with sound">Play</button>'
            elif "data-silent" in body:
                btn = ""
            else:
                btn = '<button class="vb vb--sound" type="button" aria-pressed="false" aria-label="Turn sound on">Sound</button>'
            body = body.replace("</video>", "</video>" + btn, 1)
        out.append("      " + head + body)
    css.append(f"  .{class_name}{{aspect-ratio:100/{bottom:.2f}}}")
    for i, (l, t, w) in enumerate(pos, 1):
        css.append(f"  .{class_name} .ph:nth-child({i}){{left:{l:.2f}%;top:{t:.2f}%;width:{w:.2f}%}}")
    open_tag = re.sub(r'class="collage[^"]*"', f'class="collage {class_name}"', open_tag)
    return open_tag + "\n" + "\n".join(out) + "\n    " + f"</{tag}>"

m = re.search(r'<nav class="collage[^"]*"[^>]*>.*?</nav>', html, re.S)
html = html[:m.start()] + rebuild(m.group(0), "hero", "collage--hero", hero=True) + html[m.end():]
for m in list(re.finditer(r'<article class="project" id="([\w-]+)">.*?</article>', html, re.S)):
    slug, block = m.group(1), m.group(0)
    cm = re.search(r'<div class="collage[^"]*">.*?</div>(?=\s*</article>)', block, re.S)
    block = block[:cm.start()] + rebuild(cm.group(0), slug, f"collage--p-{slug}") + block[cm.end():]
    html = html.replace(m.group(0), block)
json.dump(layouts, open(LAY, "w"), indent=1)
ms = html.index("/* LAYOUTS-M:BEGIN */"); me = html.index("/* LAYOUTS-M:END */")
html = html[:ms] + "/* LAYOUTS-M:BEGIN */ /* phone hero, generated by tools/layout.py */\n" + "\n".join(css_m) + "\n  " + html[me:]
start = html.index("/* LAYOUTS:BEGIN */"); end = html.index("/* LAYOUTS:END */")
html = html[:start] + "/* LAYOUTS:BEGIN */ /* generated by tools/layout.py — edit tools/layouts.json (manual: true) to override */\n" + "\n".join(css) + "\n  " + html[end:]
open("index.html", "w").write(html)
print(f"composed {sum(1 for k in layouts)} collages, {len(css)} rules")
