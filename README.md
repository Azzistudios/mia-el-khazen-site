# Mia El Khazen — Website

Single-page portfolio for Mia El Khazen, architect and production
designer in Paris. Built from the brief in `brief/Website.pdf`:
paper hero with a dense collage of all fifteen project covers, a
text-only About section, then a vivid-blue run of fifteen project blocks.

## Local development

```bash
python3 serve.py          # serves the root at http://localhost:3000
python3 serve.py 3010     # …or any other port if 3000 is busy
./screenshot.sh http://localhost:3000/ shots/desktop.png 1440 6400
```

## Adding project images

Drop a source folder for each project in the project root, named
`NN_Name/` (for example `01_Bluebay/`), with the photos inside at any
size. Then:

1. Add the folder to `SOURCES` in `build_images.py` — its slug, the order
   of the files as they should appear in the block, and which file is the
   hero cover.
2. Run `python3 build_images.py`. It writes web-sized JPGs (1600px long
   edge, quality 85) to `images/<slug>/01.jpg…` plus `cover.jpg`. Videos
   listed under `"videos"` become `video-NN.mp4` (720p H.264 at 2.5 Mbps
   with AAC audio, playable in every browser) and a `video-NN-poster.jpg`
   frame. Conversion uses the Swift scripts in `tools/` (AVFoundation),
   so it works on this Mac without ffmpeg. Phone HEVC clips must go
   through this step: Chrome and Firefox will not play them as-is.
   Per clip: `"audio": False` drops a silent track (loops then play
   without controls), `"copy": True` keeps a file untouched (e.g. a
   low-res 360p download that re-encoding would only bloat), and a
   `"cover": "video-01"` uses that clip's poster as the hero image.
   Long recordings get `data-autoplay="off"` in the HTML so they only
   play on request (see The Fridge's full concert).
3. Run `python3 tools/layout.py`. It composes each project collage as an
   editorial stack: one piece per row, never two side by side, the lead
   wide and flush left, the rest zigzagging flush right / flush left at a
   few fixed widths, with the same gutter under every piece in every
   project; every slot keeps the exact aspect ratio of its photo or clip
   (nothing is ever cropped), and the CSS between the `LAYOUTS` markers
   in `index.html` is regenerated. The result is recorded in
   `tools/layouts.json`; to place a project by hand, set `"manual": true`
   on its key and edit the slots, then run the tool again. The tool also
   inserts the video buttons, so re-run it whenever
   media changes. Videos play muted while in view and pause off-screen;
   the Sound pill turns audio on for one clip at a time, and long
   recordings wait for Play.

Source folders, `brief/` and `shots/` are excluded from deploys by
`.vercelignore`. Missing images simply leave a grey slot.

The hero is a dense, messy pile of all fifteen project covers, each linking to its project and showing its `cover.jpg`,
or its `01.jpg` if there is no cover: pieces of contrasting sizes sit on one another, some bleed off the sides,
and x positions snap to a loose grid so it reads as composed rather than random. Desktop and phones get their own
arrangement; run `python3 tools/layout.py --reseed` to reshuffle.

## Tech

- Vanilla HTML / CSS — no build step, all styles inline in `index.html`
- Anton + Bebas Neue from Google Fonts (the two faces embedded in the brief)
- Flat paper background with a CSS/SVG grain; on phones, project collages keep the same one-per-row
  zigzag stack (clips full width), while the hero keeps its own overlapping arrangement
- Slim top bar that appears once the hero scrolls away, numbered project headers, a gentle reveal on
  scroll (off under reduced motion), and a footer with email, phone and back-to-top
- Colours and type rules: `brand_assets/COLOURS.md`
- `vercel.json` for deploy (clean URLs, cache and security headers)

## Still to do

- All fifteen projects have their media in place (8 Sep 2026). Self-hosted video now totals ~200 MB; if the site
  grows further, move the clips to a video host (e.g. Cloudinary) and keep the slots as they are
- Social links (Instagram etc.) if wanted — the footer has email and phone
