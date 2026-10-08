#!/usr/bin/env python3
"""Compose every collage as a staggered, gutter-consistent arrangement in which each
photo or clip keeps its exact aspect ratio (nothing is ever cropped).

    python3 tools/layout.py

How a project collage is built (the user's 8 Oct 2026 note: "same gutter in every section,
well spaced, medias not side by side, more aligned"):
  • an editorial stack: one piece per row, never two side by side; the lead sits flush left
    at a wide width, the rest alternate flush right / flush left at one of three fixed widths
    (landscape, square, portrait) so edges line up from project to project;
  • the same gutter (GUT) separates every piece in every project;
  • the result is written as absolute positions (left / top / width in % of the collage
    width) into the CSS between the LAYOUTS markers, and each slot gets
    style="aspect-ratio:W/H" from its own file so its height follows its media.
The hero is different: scatter() piles all fifteen covers on one another (see its docstring).
tools/layouts.json records the generated slots; set "manual": true on a key and edit its
slots to take over by hand. Also inserts the sound / play buttons.
Run after build_images.py, and after editing layouts.json.
"""
import json, os, random, re, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
GUT = 2.2                     # the one gutter under every piece of every project, % of collage width (tightened 8 Oct 2026: "too separated")
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

# air: gap under a piece (fraction of the narrower width); bite: how far a piece sits on the one
# below (fraction of the narrower width); p_bite: share of pieces that overlap; hpad: pieces
# closer than this side by side count as stacked; jitter: how far the top row drifts off one line;
# snap: x positions sit on this grid so edges line up now and then (the editorial part)
DESKTOP = dict(widths=(10, 13, 16, 24, 32, 40), bleed=6.0, first=36, target=70, air=(0.0, 0.05), bite=(0.18, 0.48),
               p_bite=0.9, hpad=-6.0, min_vis=0.52, cover=0.76, jitter=8.0, snap=3.0)
MOBILE  = dict(widths=(34, 40, 48, 58, 68), bleed=8.0, first=62, target=230, air=(0.0, 0.05), bite=(0.15, 0.42),
               p_bite=0.85, hpad=-8.0, min_vis=0.52, cover=0.76, jitter=6.0, snap=4.0)

def scatter(aspects, seed=58, tries=160, widths=DESKTOP["widths"], bleed=2.0, first=30, air=(0.12, 0.34),
            bite=(0.05, 0.12), p_bite=0.3, hpad=2.4, min_vis=0.9, jitter=0.0, snap=0.0, **_):
    """Dense, messy collage for the hero after Reference.png (the user asked on 6 Oct 2026 for
    all fifteen projects, "more crowded, not organized", and on 8 Oct 2026 for "more messy,
    pics on each other, but in an editorial way"): pieces of different sizes piled on one
    another, nearly every one sitting well onto a neighbour, some bleeding off the sides,
    small gaps only. `min_vis` keeps enough of every piece visible to read it.

    Editorial, not random: a small piece tends to follow (and land on) a big one and vice
    versa, so the pile has scale contrast; x positions snap to a loose grid so edges line up
    here and there; the top row drifts (`jitter`) instead of sitting on one line.

    Each piece gets its own random width and its own spacing (a gap, or with probability
    p_bite an overlap) *before* positions are tried, so choosing the highest free spot
    cannot quietly favour the tightest spacing. Pieces closer than `hpad` side by side count
    as stacked, so nothing sits flush against a neighbour. Seeds live in tools/layouts.json;
    `--reseed` searches for the most balanced arrangement."""
    rnd = random.Random(seed)
    SX, SY = 6, 4
    placed = []
    small = widths[:len(widths) // 2]; big = widths[len(widths) // 2:]
    last = first
    for i, a in enumerate(aspects):
        if i == 0:
            w = first
        else:
            r = rnd.random()
            pool = small if (last in big or last == first) and r < 0.7 else big if last in small and r < 0.6 else widths
            w = pool[rnd.randrange(len(pool))]
        last = w
        h = w / a
        frac = rnd.uniform(*bite) if rnd.random() < p_bite else -rnd.uniform(*air)   # >0 overlap, <0 air
        best = fallback = None
        for _ in range(tries):
            x = rnd.uniform(-bleed, 100 - w + bleed)
            if snap:
                x = round(x / snap) * snap
            y = rnd.uniform(0, jitter) if jitter else 0.0
            for (px, py, pw, ph, _p) in placed:
                if x < px + pw + hpad and px < x + w + hpad:
                    # how far it sits onto the piece below, as a share of *that* piece's height:
                    # a small cover can land well inside a big one, a big one only nips a small one
                    y = max(y, py + ph - (ph if frac > 0 else min(w, pw)) * frac)
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
        return evenness(slots, aspects, params["target"], params.get("cover")) - max(0, 0.6 - min(vis)) * 4   # nobody buried
    return max(seeds, key=score)

def width_for(a, lead=False):
    """Three fixed widths by shape (one more set for the lead) so edges line up across projects
    and every piece reads at a similar height whatever its aspect."""
    if a < 0.8:   return 40 if lead else 36      # portrait
    if a < 1.2:   return 54 if lead else 46      # square-ish
    return 70 if lead else 58                    # landscape, clips

def compose(aspects, hero=False):
    """Editorial stack: one piece per row (never side by side), the lead flush left and wide,
    the rest zigzagging flush right / flush left, the same GUT under each. See the module doc."""
    slots = []
    top = 0.0
    for i, a in enumerate(aspects):
        w = width_for(a, lead=(i == 0))
        left = 0 if i % 2 == 0 else 100 - w
        slots.append((left, top, w))
        top += w / a + GUT
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
        css_m.append(f"  .{class_name}{{display:block;aspect-ratio:100/{bm:.2f}}}")
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
