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
The hero is different: freeform() throws all fifteen covers and clips over a tall canvas (see its docstring).
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

# Hero after yasminaaoun.com (Mia, 9 Oct 2026: "the same hero section as this — the disorder of
# pics and videos and the size"): small-to-medium pieces thrown over a canvas about as tall as it
# is wide, air between most of them, a few sitting on a neighbour's corner, some running off the
# sides. widths: sizes to draw from (% of width); first: the lead; height: canvas height (% of
# width); bleed: how far a piece may run off the sides; gap: the least air between pieces that do
# not touch; p_touch: share of pieces that sit on a neighbour; bite: how much of the smaller piece
# such an overlap covers; max_touch: how many neighbours one piece may sit on; cover / inner:
# what the seed search aims for (share of the canvas covered, share of its middle covered)
DESKTOP = dict(widths=(11, 13, 15, 18, 21, 24, 28), first=26, height=92, bleed=7.0, gap=1.5, p_touch=0.5,
               bite=(0.05, 0.3), max_touch=2, min_vis=0.6, cover=0.45, inner=0.5)
MOBILE  = dict(widths=(26, 30, 34, 40, 46, 54), first=52, height=250, bleed=10.0, gap=2.5, p_touch=0.5,
               bite=(0.05, 0.3), max_touch=2, min_vis=0.6, cover=0.45, inner=0.5)

def freeform(aspects, seed=1, widths=DESKTOP["widths"], first=24, height=100, bleed=7.0, gap=2.0, p_touch=0.45,
             bite=(0.04, 0.28), max_touch=2, tries=400, **_):
    """Throw the pieces over the canvas one by one: each gets a width (big and small alternate for
    contrast), then a random spot that either keeps `gap` of air from everything or, for a
    p_touch share of them, sits on one or two neighbours' corners by a `bite` share of the
    smaller piece. Clear pieces prefer a spot with a little room around it (capped, so loose
    clusters still form). Returns (slots, how much of each piece stays visible under the ones
    drawn after it). Seeds live in tools/layouts.json; `--reseed` searches for the best."""
    rnd = random.Random(seed)
    placed = []
    small = widths[:len(widths) // 2]; big = widths[len(widths) // 2:]
    last = first
    for i, a in enumerate(aspects):
        if i == 0:
            w = first
        else:
            r = rnd.random()
            pool = small if (last in big or last == first) and r < 0.65 else big if last in small and r < 0.55 else widths
            w = pool[rnd.randrange(len(pool))]
        last = w
        h = w / a
        touch = i > 0 and rnd.random() < p_touch
        best = loose = None
        for _ in range(tries):
            x = rnd.uniform(-bleed, 100 - w + bleed)
            y = rnd.uniform(0, max(0.0, height - h))
            touches, room, ok = 0, 99.0, True
            for (px, py, pw, ph) in placed:
                ox = min(x + w, px + pw) - max(x, px); oy = min(y + h, py + ph) - max(y, py)
                if ox > 0 and oy > 0:
                    f = ox * oy / min(w * h, pw * ph)
                    if not (bite[0] <= f <= bite[1]):
                        ok = False; break
                    touches += 1
                else:
                    g = max(-ox, -oy)
                    if g < gap:
                        ok = False; break
                    room = min(room, g)
            if not ok or touches > max_touch:
                continue
            score = min(room, 4.0) + rnd.uniform(0, 4.0)
            if (touches > 0) == touch:
                if best is None or score > best[0]: best = (score, x, y)
            elif loose is None or score > loose[0]:
                loose = (score, x, y)
        if best is None and loose is None:
            x, y = rnd.uniform(0, 100 - w), rnd.uniform(0, max(0.0, height - h))    # no spot obeys the rules: drop it anywhere
        else:
            _, x, y = best or loose
        placed.append((x, y, w, h))
    SX, SY = 6, 4
    vis = []
    for i, (x, y, w, h) in enumerate(placed):
        pts = [(x + (gx + .5) * w / SX, y + (gy + .5) * h / SY) for gx in range(SX) for gy in range(SY)]
        hid = sum(1 for (qx, qy) in pts if any(px <= qx <= px + pw and py <= qy <= py + ph for (px, py, pw, ph) in placed[i + 1:]))
        vis.append(1 - hid / len(pts))
    return [(x, y, w) for (x, y, w, h) in placed], vis

def evenness(slots, aspects, target, cover=None, inner_min=0.82):
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
    score -= max(0, inner_min - sum(inner) / len(inner)) * 3.0     # no hole in the middle
    qmin = 0.55 if cover is None else cover * 0.75
    score -= max(0, qmin - min(quads)) * 3.0 + abs(cx - 50) / 60 + abs(bottom - target) / (target * 3.5)
    return score

def best_seed(aspects, params, seeds=range(1, 201)):
    def score(sd):
        slots, vis = freeform(aspects, seed=sd, **params)
        return (evenness(slots, aspects, params["height"], params.get("cover"), params.get("inner", 0.82))
                - max(0, params.get("min_vis", 0.6) - min(vis)) * 4)          # nobody buried
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
        n = len(items)
        if not RESEED and spec.get("manual") and len(spec.get("slots", [])) == n and len(spec.get("slots_m", [])) == n:
            # placed by hand in layouts.json (e.g. Mia's 10 Oct 2026 nudge of one phone piece): keep as is
            slots = [(s["left"], s["top"], s["width"]) for s in spec["slots"]]
            m_slots = [(s["left"], s["top"], s["width"]) for s in spec["slots_m"]]
            vis_d = vis_m = [1.0]
        else:
            if RESEED or "seed" not in spec:
                spec["seed"], spec["seed_m"] = best_seed(A, DESKTOP), best_seed(A, MOBILE)
            slots, vis_d = freeform(A, seed=spec["seed"], **DESKTOP)
            m_slots, vis_m = freeform(A, seed=spec["seed_m"], **MOBILE)
            spec["slots"] = [{"left": round(l, 2), "top": round(t, 2), "width": round(w, 2)} for l, t, w in slots]
            spec["slots_m"] = [{"left": round(l, 2), "top": round(t, 2), "width": round(w, 2)} for l, t, w in m_slots]
            spec["manual"] = False
        def place(sl):                         # keep the deliberate overlaps — no push-down pass
            b = max(t + w / a for (_, t, w), a in zip(sl, A))
            return b, [(l, t / b * 100, w) for (l, t, w) in sl]
        bottom, pos = place(slots)
        bm, pos_m = place(m_slots)
        print(f"hero: least-visible piece {min(vis_d):.0%} on desktop, {min(vis_m):.0%} on phones")
        css_m.append(f"  .{class_name}{{display:block;aspect-ratio:100/{bm:.2f}}}")
        css_m.append(f"  .{class_name}>.ph{{position:absolute;margin:0}}")
        for i, (l, t, w) in enumerate(pos_m, 1):
            z = spec["slots_m"][i - 1].get("z")            # hand-placed pieces may ask to sit in front ("z": 2)
            css_m.append(f"  .{class_name} .ph:nth-child({i}){{left:{l:.2f}%;top:{t:.2f}%;width:{w:.2f}%{f';z-index:{z}' if z else ''}}}")
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
        z = spec["slots"][i - 1].get("z") if spec.get("manual") else None
        css.append(f"  .{class_name} .ph:nth-child({i}){{left:{l:.2f}%;top:{t:.2f}%;width:{w:.2f}%{f';z-index:{z}' if z else ''}}}")
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
