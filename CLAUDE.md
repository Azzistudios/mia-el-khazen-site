# CLAUDE.md — Frontend Website Rules

## Always Do First
- **Invoke the `frontend-design` skill** before writing any frontend code, every session, no exceptions.
- Read `brand_assets/COLOURS.md` and glance at `brief/reference-render.png` (the approved layout).

## Project specifics — Mia El Khazen
- One page, `index.html`, all styles inline. Structure is fixed by `brief/Website.pdf`: hero (name, roles, ABOUT ME link, overlapping collage of all fifteen projects) → About (heading, two paragraphs, services line; text only — the portrait and its blue block were removed on 8 Oct 2026 at the user's request, the text keeps the measure of the old left column) → blue Work section with 15 project blocks separated by thin rules.
- Type: **Anton** for name, roles, nav, headings, project titles and descriptions. **Bebas Neue** for the about paragraph and services line. Nothing else.
- Domain: **miaelkhazen.com** (registered at GoDaddy). Canonical, og:url, share image (`brand_assets/og-image.jpg`, rendered from `tools/og.html`), `sitemap.xml` and a www→apex redirect in `vercel.json` are in place. Hosted on Vercel from `github.com/Miak-max/mia-el-khazen-site`; every push to `main` redeploys.
- Colours: vivid blue `#0c0ce4`, paper `#f8f8f7` with a faint SVG grain and **no grid lines** (user removed them 8 Sep 2026), ink `#111111`, placeholder grey `#cbd1d8`. No other colours.
- The hero is a **free scatter of all fifteen projects** after yasminaaoun.com, which is what `Reference.png` is a screenshot of (Mia, 9 Oct 2026: "the same hero section as this — the disorder of pics and videos and the size"; earlier notes 6 and 8 Oct: all 15 projects, "more collage looking", "pics on each other", editorial). Small-to-medium pieces (about a tenth to a quarter of the width) are thrown over a canvas nearly as tall as it is wide, with air between most of them, a few sitting on a neighbour's corner, some running off the sides (the hero collage is full-bleed); hovering lifts a piece. Nothing is aligned on purpose. No titles or captions. Each piece is `<a class="ph" href="#<slug>">` showing `images/<slug>/cover.jpg`, except four that are muted clips: `<a class="ph ph--video">` around `<video … muted loop playsinline preload="none" data-silent>` (the lightest files: Microfest 03, Interlude 06 05, IFxA 02 01, Interlude 07 02; they play in view, no Sound pill, click follows the link). `freeform()` in `tools/layout.py` generates separate desktop and phone arrangements (`hero.seed`, `hero.seed_m` in `tools/layouts.json`); `python3 tools/layout.py --reseed` searches for the best spread with no hole in the middle and no buried piece.
- Source photos arrive as `NN_Name/` folders in the project root (e.g. `01_Bluebay/`). Map each in `SOURCES` inside `build_images.py` (photos in `order`, clips in `videos`), run it, then adjust that project's slots and add a `.collage--<slug>` layout if the count differs from four. Videos are transcoded to 720p H.264 by `tools/transcode.swift` (no ffmpeg on this Mac) and shown as `<figure class="ph ph--wide ph--video"><video muted loop playsinline controls poster=…>` (the script strips `controls` and adds the Sound pill; `controls` stays in the HTML only as the no-JS fallback). Silent loops carry `data-silent` (no pill); long recordings get `data-autoplay="off"` + `preload="none"` and a Play button. Layout classes are generated per collage (`collage--hero`, `collage--p-<slug>`). Source folders `01_…`–`15_…` map to slugs in `build_images.py` (`06_Imagine x Automatic` → IFxA 01, `15_Imagine x Automatic 0307` → IFxA 02, `14_Interlude Bekaata` → Interlude 07 - Lebanon Concert). Never edit or delete the source folders. Media Mia asked to drop (6 Oct 2026) is removed from `index.html` and `images/` only: Microfest 03, IFxA 01 07, Interlude 01 01+03, Interlude 03 02, Interlude 05 01+04, Interlude 06 photos 01+02 and clips 01, 02, 04 (solo guitarist and Snippet 4); on 9 Oct 2026 (crossed out on phone screenshots) Paname All Starz 03, Le Sample 04 and Interlude 05 03 (its hero cover still shows that image; the hero fallback now points at 02); a rebuild may regenerate those files but they stay unused.
- Image slots are `<figure class="ph"><img src="images/…" onerror="this.remove()"></figure>`: missing files stay grey. Do not replace them with `placehold.co`.
- **Never crop media.** Every slot carries `style="aspect-ratio:W/H"` from its own photo or poster, set by `tools/layout.py`. That tool *composes* each project collage as an editorial stack (8 Oct 2026, the user: "same gutter in every section, well spaced, medias not side by side, more aligned"): one piece per row, never two side by side; the lead flush left and wide (70 / 54 / 40 % by shape), the rest zigzag flush right / flush left at one of three fixed widths (landscape 58, square 46, portrait 36 %), and the one `GUT` (2.2 %, tightened the same day: "too separated") under every piece. It regenerates the CSS between the `LAYOUTS` markers; phones use the same stack in CSS (84 % wide, even pieces right-aligned, clips full width). `tools/layouts.json` records the result; set `"manual": true` on a key and edit its slots to place by hand. Run it after every `build_images.py` change. The user rejected a tidy justified-rows grid (9 Sep 2026) and the staggered masonry columns (8 Oct 2026): do not go back to either.
- Design layer added 9 Sep 2026 at the user's request ("more appealing and design led", same identity): slim fixed `.topbar` that appears after the hero (paper on paper, blue over the Work section), `SELECTED WORK / 15 PROJECTS` label, numbered project headers (`.project__num`, Bebas) with Bebas descriptions, reveal-on-scroll on `.ph` (opacity/transform only, off under reduced motion), custom video buttons (`.vb--sound` pill toggles mute, one clip with sound at a time; `.vb--play` for `data-autoplay="off"` recordings, which then show native controls), and a `.foot` footer (name, roles, Paris, mia.elk.pro@gmail.com, +33 6 51 35 63 10, Work/About/Top links). Hero captions were removed on 10 Sep 2026 at the user's request — do not add titles to the hero. Keep all of it inside Anton + Bebas + blue + paper.
- The reveal means `.ph` starts at opacity 0 when JS runs; `shots/frame.html` adds `.in` to every slot before capturing.

## Reference Images
- If a reference image is provided: match layout, spacing, typography, and color exactly. Swap in placeholder content. Do not improve or add to the design.
- If no reference image: design from scratch with high craft (see guardrails below).
- Screenshot your output, compare against reference, fix mismatches, re-screenshot. Do at least 2 comparison rounds. Stop only when no visible differences remain or user says so.

## Local Server
- **Always serve on localhost** — never open a `file:///` URL.
- Start the dev server: `python3 serve.py` (serves the project root at `http://localhost:3000`). Port 3000 is often held by another site's `serve.py` — check with `lsof -nP -iTCP:3000 -sTCP:LISTEN` and, if taken, run `python3 serve.py 3010` instead. Never kill the other server.
- `serve.py` lives in the project root. Start it in the background before previewing.
- If the server is already running, do not start a second instance.

## Screenshot Workflow
- Headless Chrome is available: `./screenshot.sh <url> <out.png> [width] [height]` (use a tall height, e.g. 6400, for a full-page capture).
- Headless Chrome will not go narrower than 500px and ignores `#anchor` scrolling. Use `shots/frame.html`: `?w=390` for mobile (capture at 600px wide, crop the left 390px), `?w=1976&id=<slug>` to put one project block at the top, and `&h=2000` to cap the frame height (a full-page frame loads all 19 videos and Chrome can get killed for memory).
- Save captures under `shots/` (git-ignored). Compare against `brief/reference-render.png`.

## Brand Assets
- Always check `brand_assets/` before designing. `portrait-mia.png` there is the full-resolution cutout, kept for reference only: the site has had no portrait since 8 Oct 2026 (the web copies in `images/` were deleted).
- **Never** pull projects, images, copy or branding from any other site. This is Mia's own portfolio; the brief in `brief/` and her source folders are the only content sources.
- If assets exist there, use them. Do not use placeholders where real assets are available.

## Anti-Generic Guardrails
- **Colors:** Never introduce colours outside the brand tokens.
- **Typography:** Anton and Bebas Neue only. Tight line-height on display sizes (`.9`–`1`), `1.12` on Bebas body copy.
- **Animations:** Only animate `transform` and `opacity`. Never `transition-all`.
- **Interactive states:** Every clickable element needs hover, focus-visible, and active states. No exceptions.
- **Spacing:** vw-based rhythm measured from the brief (`--margin: 5.7vw`). Don't introduce arbitrary pixel values.

## Hard Rules
- Do not add sections, features, or content not in the reference
- Do not "improve" a reference design — match it
- Do not stop after one screenshot pass
- Do not use `transition-all`
